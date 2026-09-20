import uvicorn
from app.config import settings

def main():
    print(f"Starting Autonomous AI Agent server on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

if __name__ == "__main__":
    main()

