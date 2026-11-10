```powershell
# 启动后端（在项目根目录的终端执行）
conda activate aiinterview
python -m uvicorn backend.main:app --reload
```

```powershell
# 启动前端（在项目根目录另开一个终端执行）
conda activate aiinterview
python -m streamlit run frontend/app.py
```

```powershell
# 执行管理员初始化（在项目根目录的终端执行）
conda activate aiinterview
python -m backend.init_admin
```
