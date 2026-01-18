import glob
import json
import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.pipeline.data_pipeline import PharmaDataPipeline
from app.pipeline.data_quality import DataQualityMonitor

pipeline_bp = Blueprint('pipeline', __name__)
logger = logging.getLogger(__name__)

pipeline = PharmaDataPipeline()
quality_monitor = DataQualityMonitor()


@pipeline_bp.route('/pipeline/run', methods=['POST'])
def run_pipeline():
    """Run the data pipeline"""
    try:
        payload = request.get_json(silent=True) or {}
        data_type = payload.get('data_type')

        if data_type:
            success = pipeline.run_etl_pipeline(data_type)
            message = f"{data_type.capitalize()} pipeline completed"
        else:
            results = pipeline.run_daily_pipeline()
            success = all(status == 'Success' for status in results.values())
            message = 'Daily pipeline completed'

        if success:
            return (
                jsonify(
                    {
                        'success': True,
                        'message': message,
                        'timestamp': datetime.now().isoformat(),
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    'success': False,
                    'message': 'Pipeline failed',
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            500,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(f"Pipeline error: {str(e)}")
        return (
            jsonify(
                {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            500,
        )


@pipeline_bp.route('/pipeline/status', methods=['GET'])
def get_pipeline_status():
    """Get pipeline status and statistics"""
    try:
        stats_file = 'reports/pipeline_stats.json'
        stats = {
            'last_run': None,
            'status': 'unknown',
            'statistics': {},
        }

        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        else:
            pattern = 'reports/pipeline_stats_*.json'
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getmtime)
                with open(latest_file, 'r') as f:
                    stats = json.load(f)

        return (
            jsonify(
                {
                    'success': True,
                    'status': 'running' if stats.get('status') == 'success' else 'idle',
                    'last_run': stats.get('last_run'),
                    'statistics': stats.get('statistics', stats),
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pipeline_bp.route('/pipeline/quality', methods=['GET'])
def check_data_quality():
    """Run data quality check"""
    try:
        report = quality_monitor.run_comprehensive_quality_check()

        return (
            jsonify(
                {
                    'success': True,
                    'report': report,
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(f"Quality check error: {str(e)}")
        return (
            jsonify(
                {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            500,
        )


@pipeline_bp.route('/pipeline/generate-sample', methods=['POST'])
def generate_sample_data():
    """Generate sample data for testing"""
    try:
        data = request.get_json() or {}
        data_type = data.get('data_type', 'drugs')
        num_records = data.get('records', 100)

        sample_df = pipeline.generate_sample_data(data_type, num_records)

        os.makedirs('data/raw', exist_ok=True)
        output_file = (
            f"data/raw/{data_type}_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        sample_df.to_csv(output_file, index=False)

        return (
            jsonify(
                {
                    'success': True,
                    'message': f'Generated {num_records} sample {data_type} records',
                    'file': output_file,
                    'records': len(sample_df),
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(f"Sample generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@pipeline_bp.route('/pipeline/logs', methods=['GET'])
def get_pipeline_logs():
    """Get pipeline logs"""
    try:
        log_file = 'logs/data_pipeline.log'

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read().split('\n')[-100:]
        else:
            logs = ['No logs available']

        return (
            jsonify(
                {
                    'success': True,
                    'logs': logs,
                    'count': len(logs),
                    'timestamp': datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:  # noqa: BLE001
        logger.error(f"Log retrieval error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
