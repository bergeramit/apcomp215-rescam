import dataloader
from abc import ABC, abstractmethod
import pandas as pd
import csv
import os

def create_complete_rows(file):
    csv.field_size_limit(2147483647)
    with open(file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        result = []
        for row in reader:
            row_dict = dict(zip(header, row))
            if row_dict['label'] in ['0', '1']:
                result_row = {
                    'sender': row_dict.get('sender', ''),
                    'receiver': row_dict.get('receiver', ''),
                    'date': row_dict.get('date', ''),
                    'subject': row_dict.get('subject', ''),
                    'body': row_dict.get('body', ''),
                    'label': int(row_dict['label']),
                    'urls': row_dict.get('urls', ''),
                    'spam_flag': int(row_dict.get('spam_flag', '0')),
                    'original_db': os.path.basename(file)
                }
                result.append(result_row)
    return result

def main():
    files = dataloader.get_raw_files_local()
    print(files)

    output_cleaned_dataset_path = os.path.join('processed-dataset', 'cleaned_dataset.parquet')
    if not os.path.exists(output_cleaned_dataset_path):
        all_cleaned_data = []
        for file in files:
            print(f"Processing file: {file}")
            all_cleaned_data.extend(create_complete_rows(file))
        
        df = pd.DataFrame(all_cleaned_data)
        df.to_parquet(output_cleaned_dataset_path, compression='snappy', engine='pyarrow')
        print(f"Cleaned data saved to {output_cleaned_dataset_path}")
    
    dataloader.upload_processed_files(output_cleaned_dataset_path)

if __name__ == "__main__":
    main()