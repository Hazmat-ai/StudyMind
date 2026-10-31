"""QA-only server. This file is not copied into the backend runtime image."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import uvicorn
from app.config import Settings
from app.main import create_app
from app.routers.generate import get_generator
from app.schemas.generate import StudyMaterial

def main():
    with tempfile.TemporaryDirectory(prefix='studymind-e2e-') as directory:
        config=Settings(app_env='testing',secret_key='e2e-only-never-a-deployed-secret'*3,database_url=f'sqlite+aiosqlite:///{directory}/qa.sqlite',require_email_verification=False,test_auto_schema=True,anthropic_api_key='test-only-no-live-provider',anthropic_model='qa-fixture')
        app=create_app(config)
        async def fixture(content,options,settings):
            return StudyMaterial(title='Relational databases',summary='Tables organize records. Keys connect related records.',flashcards=[{'term':f'Key {i+1}','definition':'A key identifies a record.'} for i in range(options.num_flashcards)],questions=[{'question':f'What is a key? ({i+1})','answer':'It identifies a record.','type':'short_answer','options':[]} for i in range(options.num_questions)],concepts=[{'term':'Keys','related':['Tables']}])
        app.dependency_overrides[get_generator]=lambda:fixture
        uvicorn.run(app,host='127.0.0.1',port=8000,access_log=False)
if __name__=='__main__':main()
