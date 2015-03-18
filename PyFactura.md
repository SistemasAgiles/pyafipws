# PyFactura #

<a href='http://www.sistemasagiles.com.ar/trac/wiki/PyFactura'><img src='http://www.pyafipws.com.ar/_/rsrc/1402698702338/inicio/aplicativo_factura_electronica_06b_ubuntu.png?height=317&width=320' align='right' border='0' /></a>

PyFactura es una aplicación libre y gratuita para generar Facturas Electrónicas de modo totalmente ad-hoc (independiente) según normativa AFIP.

El objetivo es tener una propuesta libre y abierta alternativa al Aplicativo SIAP RECE y servicios interactivos de AFIP ("Comprobantes en Linea" por clave fiscal).

Ventajas:

  * Formulario visual simple y ágil (sin problemas web de conexión, expiración de sesión, limitación en cantidad de facturas, etc.)
  * Almacenamiento de datos propios (sin necesidad de reingresar datos de clientes o descripción de productos por cada factura)
  * Flexibilidad en la configuración (por ej. generación de PDF con logos y textos adicionales arbitrarios, envió de emails, etc.)
  * Posibilidad de adaptaciones y modificaciones particulares
  * Estudio y desarrollo de bibliotecas de desarrollo rápido de aplicaciones, servicios web, extensibilidad para lenguajes/aplicaciones legadas (Visual Basic, Visual Fox Pro, Clipper, Cobol,), etc.

Utiliza varios componentes del proyecto PyAfipWs: Padrón de Contribuyentes, almacenamiento electrónico (RG1361) e interfaces y herramientas libres para servicios web AFIP (WSAA y WSFEv1).

Por el momento soporta factura electrónica mercado interno (RG2485 y normas relacionadas como la RG3571 de nuevos sujetos obligados al régimen)
En el futuro posiblemente se agregará soporte para Factura electrónica con detalle (RG2904), exportación (RG2758) y otros webservices de entidades relacionadas (remito electrónico, sistema nacional de trazabilidad, etc.).
Actualmente los datos se almacenan en una base de datos sqlite interna, pero se podría conectar con otros motores (PostgreSQL, MysQL o propietarios con PyODBC), y esta contemplado agregar soporte para archivos de intercambio (texto de ancho fijo, tablas dbf, xml, json).

Próximamente será integrado con PyRece (aplicativo simil SIAP RECE)

Direcciones útiles:

  * Repositorio en GitHub: https://github.com/reingart/pyfactura/
  * Proyecto en GoogleCode (buscar repositorio gui2py-app): https://code.google.com/p/pyafipws/
  * Documentación: http://www.sistemasagiles.com.ar/trac/wiki/PyFactura
  * Manual de Usuario (instalación y configuración): http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
  * For público para consultas y novedades (grupo de usuarios y desarrolladores en google): https://groups.google.com/forum/#!forum/pyafipws

Desde ya, toda colaboración es bienvenida
Se agradece difusión