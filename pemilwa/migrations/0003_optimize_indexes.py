from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pemilwa', '0002_remove_calon_foto_remove_calon_periode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calon',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='pemilih',
            name='sudah_memilih',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='vote',
            name='pilihan',
            field=models.CharField(choices=[('calon', 'Memilih Calon'), ('abstain', 'Abstain')], db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='vote',
            name='voted_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
