#def main():
#    print("Hello from llm-p!")


#if __name__ == "__main__":
#    main()

# main.py
from fastapi import FastAPI

app = FastAPI(title="llm-p")  # ← Обязательно имя "app"!

@app.get("/")
def read_root():
    return {"Hello": "World"}