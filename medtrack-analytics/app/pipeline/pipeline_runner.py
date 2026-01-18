import argparse
import logging
import os
import threading
import time
from datetime import datetime

import schedule

from app.pipeline.data_pipeline import PharmaDataPipeline
from app.pipeline.data_quality import DataQualityMonitor


class PipelineScheduler:
    """Schedule and manage pipeline executions"""

    def __init__(self):
        self.logger = logging.getLogger('pipeline_scheduler')
        self.pipeline = PharmaDataPipeline()
        self.quality_monitor = DataQualityMonitor()
        self.running = False

    def run_daily_etl(self):
        """Run daily ETL pipeline"""
        self.logger.info('Executing scheduled daily ETL pipeline')
        try:
            results = self.pipeline.run_daily_pipeline()
            self.logger.info(f'Daily ETL completed: {results}')
            return results
        except Exception as e:  # noqa: BLE001
            self.logger.error(f'Daily ETL failed: {str(e)}')
            return {'status': 'failed', 'error': str(e)}

    def run_quality_check(self):
        """Run data quality check"""
        self.logger.info('Executing scheduled data quality check')
        try:
            report = self.quality_monitor.run_comprehensive_quality_check()
            score = report['quality_score']['overall']
            self.logger.info(f'Quality check completed. Score: {score}')

            if score < 70:
                self.logger.warning(
                    f'Low quality score ({score}), attempting fixes...'
                )
                fixes = self.quality_monitor.fix_data_issues()
                self.logger.info(f"Applied {fixes['fixes_applied']} fixes")

            return report
        except Exception as e:  # noqa: BLE001
            self.logger.error(f'Quality check failed: {str(e)}')
            return {'status': 'failed', 'error': str(e)}

    def run_backup(self):
        """Run database backup (simulated)"""
        self.logger.info('Executing scheduled backup')
        self.logger.info('Backup completed (simulated)')
        return {'status': 'success', 'backup_time': datetime.now().isoformat()}

    def setup_schedule(self):
        """Setup scheduled tasks"""
        schedule.every().day.at('02:00').do(self.run_daily_etl)
        schedule.every(6).hours.do(self.run_quality_check)
        schedule.every().day.at('00:00').do(self.run_backup)

        self.logger.info('Pipeline schedule setup complete')

    def start(self):
        """Start the scheduler"""
        self.running = True
        self.setup_schedule()

        self.logger.info('Pipeline scheduler started')

        self.run_daily_etl()
        self.run_quality_check()

        thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        thread.start()

        return thread

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.logger.info('Pipeline scheduler stopped')

    def run_once(self, task_name):
        """Run a specific task once"""
        tasks = {
            'etl': self.run_daily_etl,
            'quality': self.run_quality_check,
            'backup': self.run_backup,
        }

        if task_name in tasks:
            self.logger.info(f'Manually running task: {task_name}')
            return tasks[task_name]()
        raise ValueError(f'Unknown task: {task_name}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler(),
        ],
    )

    parser = argparse.ArgumentParser(description='Pharma Data Pipeline Runner')
    parser.add_argument(
        'command',
        choices=['run', 'start', 'stop', 'etl', 'quality', 'backup', 'generate'],
        help='Command to execute',
    )
    parser.add_argument(
        '--data-type',
        choices=['drugs', 'sales', 'patients'],
        help='Data type for generate command',
    )
    parser.add_argument(
        '--records', type=int, default=100, help='Number of records to generate'
    )

    args = parser.parse_args()

    scheduler = PipelineScheduler()

    if args.command == 'start':
        scheduler.start()
        print('Scheduler started. Press Ctrl+C to stop.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()

    elif args.command == 'run':
        scheduler.setup_schedule()
        scheduler.run_daily_etl()
        scheduler.run_quality_check()

    elif args.command == 'etl':
        scheduler.run_daily_etl()

    elif args.command == 'quality':
        scheduler.run_quality_check()

    elif args.command == 'backup':
        scheduler.run_backup()

    elif args.command == 'generate':
        if not args.data_type:
            print('Error: --data-type is required for generate command')
        else:
            pipeline = PharmaDataPipeline()
            sample_data = pipeline.generate_sample_data(
                args.data_type, args.records
            )

            os.makedirs('data/raw', exist_ok=True)
            output_file = f'data/raw/{args.data_type}_sample.csv'
            sample_data.to_csv(output_file, index=False)
            print(
                f'Generated {args.records} sample {args.data_type} records to {output_file}'
            )

    else:
        parser.print_help()
