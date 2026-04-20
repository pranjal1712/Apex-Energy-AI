@echo off
echo 🚀 Preparing to push Apex Energy AI to GitHub...
git init
git remote add origin https://github.com/pranjal1712/Apex-Energy-AI.git
git add .
git commit -m "feat: setup AWS Docker deployment with CI/CD pipeline"
git branch -M main
echo ⬆️ Pushing to main branch...
git push -u origin main
echo ✅ Done! Your code is now on GitHub.
pause
