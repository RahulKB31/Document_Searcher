import psycopg2
import pandas as pd
import os

def load_data(output_dir, logger=None):
    os.makedirs(output_dir, exist_ok=True)
    log_filename = 'data_export.log'
    table_names = ['erp.workflows_objects_takt', 'erp.workflows_objects_task', 'staging.shop_floors', 'staging.workflow_groups']

    # Delete previous files, except the log file
    for filename in os.listdir(output_dir):
        if filename == log_filename:
            continue
        file_path = os.path.join(output_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                if logger:
                    logger.info(f"Deleted: {file_path}")
        except Exception as e:
            if logger:
                logger.error(f'Error deleting file {file_path}: {e}')

    # Database Connection and Export
    try:
        conn = psycopg2.connect(
            dbname='ost2',
            user='postgres',
            password='prodstat537(',
            host='10.187.190.17',
            port='5432'
        )

        if logger:
            logger.info('Database Connection Established')

        for table in table_names:
            query = f"SELECT * FROM {table};"
            # Replace . with _ for filename: erp.workflows_objects_task.xlsx -> erp_workflows_objects_task.xlsx
            safe_filename = table.replace('.', '_') + ".json"
            out_file = os.path.join(output_dir, safe_filename)

            try:
                df = pd.read_sql(query, conn)
                df.to_json(out_file, orient='records', lines=True)
                if logger:
                    logger.info(f"Saved: {out_file}")
            except Exception as e:
                if logger:
                    logger.error(f"Error processing table {table}: {e}")
    except Exception as db_e:
        if logger:
            logger.error(f"Database connection failed: {db_e}")
    finally:
        if 'conn' in locals():
            conn.close()
            if logger:
                logger.info("Database connection closed.")