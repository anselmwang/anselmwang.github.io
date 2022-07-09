python copy.py
status=$(git status docs --short)
echo $status
if [[ status != '' ]]; then
  echo 'changed'
  git add docs/.
  git commit -m "auto commit at `date`"
  git push
else
  echo 'clean'
fi
