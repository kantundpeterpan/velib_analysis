import os 
from pyathena import connect 
from pathlib import Path
import boto3
import awswrangler as wr
import json 

__here__ = Path(__file__).parent

def load_aws_credentials():
    
    aws_access_key_id = os.getenv("aws_access_key_id".upper())
    aws_secret_access_key = os.getenv("aws_secret_access_key".upper())

    if aws_access_key_id is None or aws_secret_access_key is None:

        with open(__here__ / "../../.creds/key.json", "r") as f:
            creds = json.loads(f.read())
            
    else:
        creds = {
            'aws_access_key_id':aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key
        }

    return creds

def get_athena_conn():
    
    creds = load_aws_credentials()
    
    db = connect(
            s3_staging_dir='s3://gbfsbikesbucket', 
            region_name = 'eu-central-1',
            **creds
        )
    
    # aws_access_key_id = os.getenv("aws_access_key_id".upper())
    # aws_secret_access_key = os.getenv("aws_secret_access_key".upper())

    # if aws_access_key_id is None or aws_secret_access_key is None:

    #     with open(__here__ / "../../.creds/key.json", "r") as f:
    #         creds = json.loads(f.read())
            
    #     db = connect(
    #         s3_staging_dir='s3://gbfsbikesbucket', 
    #         region_name = 'eu-central-1',
    #         **creds
    #     )
        
    # else:
    #     db = connect(
    #         s3_staging_dir='s3://gbfsbikesbucket', 
    #         region_name = 'eu-central-1',
    #         aws_access_key_id = aws_access_key_id,
    #         aws_secret_access_key =aws_secret_access_key
    #     )
        
    return db


def get_boto3_session():
    
    creds = load_aws_credentials()
    session = boto3.Session(**creds, region_name='eu-central-1')
    
    return session

def save_df_aws_parquet(df, table: str,
                        path: str = "s3://gbfsbikesbucket/paris/",
                        database: str = 'paris',
                        session = get_boto3_session()):
    
    info = wr.s3.to_parquet(
        df = df, 
        path = path, 
        database = databse,
        table=table,
        boto3_session=session,
        dataset = True)
    
    return info