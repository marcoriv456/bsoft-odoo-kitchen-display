# BSOFT Kitchen Display — Odoo 17 Community

Módulo original para pantalla Kanban de cocina con estaciones, filtros por categoría/POS, estados por línea, cronómetro, alertas visuales y grupos de seguridad.

## Cómo se conserva el trabajo de cocina

La pantalla usa `bsoft.kitchen.ticket` como su fuente de datos. Un ticket es
una unidad persistente de trabajo de cocina: conserva el producto, cantidad,
nota, estación y estado aun cuando el TPV vuelva a guardar la orden. Se enlaza
con la orden POS y con el `uuid` estable de la línea que envía el TPV.

Esto es importante porque Odoo elimina y recrea las filas `pos.order.line` al
actualizar una orden de restaurante abierta. Después de cada sincronización
POS, el módulo compara las líneas actuales contra los tickets ya registrados:

- La misma línea y cantidad no crea otro ticket.
- Una línea nueva crea un ticket nuevo.
- Si aumenta la cantidad de una línea existente, sólo se crea un ticket por la
  diferencia.
- Si se reduce o elimina una línea antes de iniciarla, se ajusta o cancela el
  ticket pendiente correspondiente.
- Un producto sustituido cancela su trabajo aún pendiente y genera trabajo para
  el producto nuevo; los tickets entregados quedan como historial.

Los campos `kitchen_*` que existen en `pos.order.line` se conservan sólo para
compatibilidad con instalaciones anteriores. La pantalla y sus transiciones ya
no dependen de ellos.

## Instalación en Ubuntu
Ejemplo: addons personalizados en `/opt/odoo/custom-addons`. Ajusta la ruta a tu instalación real.

```bash
sudo mkdir -p /opt/odoo/custom-addons
sudo unzip bsoft_kitchen_display.zip -d /opt/odoo/custom-addons/
sudo chown -R odoo:odoo /opt/odoo/custom-addons/bsoft_kitchen_display
```

En `/etc/odoo.conf`, asegúrate de incluir la ruta en `addons_path`, por ejemplo:
```ini
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
```

Reinicia y revisa el log:
```bash
sudo systemctl restart odoo
sudo journalctl -u odoo -n 100 --no-pager
```

En Odoo: activa modo desarrollador → Apps → Actualizar lista → busca “BSOFT Kitchen Display” → Instalar. Asigna los grupos Cocinero, Encargado de cocina o Administrador de cocina a los usuarios. En el menú Kitchen Display crea estaciones, por ejemplo Cocina, Bebidas y Postres, y asigna categorías y puntos de venta.

## Pruebas de aceptación
1. Crea categorías de TPV para cocina y bebidas; crea estaciones coincidentes.
2. Crea pedidos desde una sesión de TPV de prueba y confirma la asignación de líneas.
3. Comprueba el flujo Pendiente → Preparando → Listo → Entregado.
4. En una orden abierta, entrega un producto, agrega otro producto desde el
   TPV y vuelve a guardar: la pantalla debe mostrar sólo el producto agregado.
4. Abre dos pantallas y verifica que los cambios se reflejen en ambas.
5. Prueba los límites de advertencia y crítico.
6. Prueba permisos de cada grupo.
7. Prueba pedidos de restaurante con mesa, notas, variantes, descuentos, cancelaciones y devoluciones.
8. Revisa logs del servidor y consola del navegador.

## Alcance y advertencias de esta entrega
Esta es una primera versión de código fuente para validar en staging, no un paquete certificado para producción. La pantalla usa notificación bus con respaldo de consulta cada 5 segundos. La asignación automática dirige cada línea a una sola estación (la primera que coincida); no duplica una línea en varias estaciones. Las particularidades de sincronización del TPV, notas y cancelaciones deben probarse contra la revisión exacta de Odoo 17 instalada. Haz copia de seguridad de base de datos y filestore antes de instalar en producción.
