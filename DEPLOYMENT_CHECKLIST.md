# Caldero Verde — lista final antes de publicar

No ejecutar estos pasos hasta recibir aprobación explícita para desplegar.

## 1. Verificación local

- [x] `python -m unittest discover -s tests -v` termina sin errores.
- [x] `node --experimental-strip-types --test tests-js/*.test.mjs` termina sin errores.
- [x] Inventario, recetas y sobras cargan desde `/api/bootstrap`.
- [x] La Secret Key no aparece en `frontend/` ni Git.

## 2. Supabase

- [x] Revisar y ejecutar `prepare_inventory_transaction`.
- [x] Verificar que `anon` y `authenticated` no puedan ejecutar esa función.
- [x] Ejecutar `seed_puerto_rican_recipe_library`.
- [ ] Probar que una receta descuenta todo de forma atómica.
- [x] Ejecutar los asesores de seguridad y rendimiento.

## 3. Netlify

- [x] Configurar `SUPABASE_URL` como variable de servidor.
- [x] Configurar `SUPABASE_SECRET_KEY` como secreto.
- [x] Configurar `APP_ACCESS_PIN` como secreto.
- [ ] Crear primero un deploy preview único.
- [x] Probar lectura pública y una escritura controlada sin insertar datos.
- [x] Publicar a producción después de aprobación explícita.

## 4. GitHub

- [x] Confirmar que `.env`, `.venv`, `node_modules` y `.netlify` estén ignorados.
- [x] Revisar el diff del proyecto.
- [x] Crear un commit del MVP solamente después de aprobar los cambios.
