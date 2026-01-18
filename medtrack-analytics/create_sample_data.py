from app.pipeline.data_pipeline import PharmaDataPipeline
import os


if __name__ == '__main__':
    for path in ['data/raw', 'data/processed', 'data/archive', 'reports', 'logs']:
        os.makedirs(path, exist_ok=True)

    pipeline = PharmaDataPipeline()

    print('Generating sample data...')
    for data_type in ['drugs', 'sales', 'patients']:
        sample_df = pipeline.generate_sample_data(data_type, 1000)
        output_file = f'data/raw/{data_type}_sample.csv'
        sample_df.to_csv(output_file, index=False)
        print(f'Generated {len(sample_df)} {data_type} records to {output_file}')

    print('\nSample data generation complete!')
