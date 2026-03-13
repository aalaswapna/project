## Local Run (No Retraining)

### 1) One-time setup
```powershell
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2) Start backend API (Terminal 1)
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 3) Start frontend UI (Terminal 2)
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open: `http://127.0.0.1:5173`
Use the auth screen to either `Login` or `Signup`.

## Full Pipeline (Downloads + training + app launch)
Use only when you explicitly want to rebuild datasets/models:
```powershell
python run.py
```
