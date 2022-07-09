python copy.py
status=$(git diff --short)
echo status
if [[ status != '' ]]; then
  echo 'changed'
  git add .
  git commit -m "auto commit at `date`"
  git push
else
  echo 'clean'
fi
