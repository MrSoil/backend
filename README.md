python manage.py makemigrations --dry-run sugr_backend
python manage.py migrate --fake backend sugr_backend zero
python manage.py makemigrations

python manage.py runserver 
