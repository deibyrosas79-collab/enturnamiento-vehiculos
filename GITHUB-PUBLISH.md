# Publicar en GitHub

## Comandos base

```powershell
cd C:\Users\deiby\Downloads\enturnamiento-vehiculos
git init
git add .
git commit -m "feat: enturnamiento con calidad, qr y geocerca"
```

## Conectar el repositorio remoto

```powershell
git remote add origin https://github.com/TU-USUARIO/TU-REPO.git
git branch -M main
git push -u origin main
```

## Antes de subir

- Revisa que no quieras publicar datos operativos reales.
- `data/enturnamiento.db` esta ignorada por `.gitignore`.
- `uploads/` esta ignorado por `.gitignore`.
- Crea usuarios definitivos y cambia las claves iniciales.
- Ajusta `android-quality-app/gradle.properties` con tu URL real de Render cuando ya exista.
