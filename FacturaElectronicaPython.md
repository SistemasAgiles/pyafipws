# Ejemplo básico desde Python #

Código de ejemplo en el lenguaje python para obtener CAE de una factura electrónica AFIP (ver [manual](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#ServicioWebdeFacturaElectrónicaMercadoInternoVersión1WSFEv1) y [info general](http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1)):

```
#!/usr/bin/python
# -*- coding: utf8 -*-

# importar modulos python
import datetime

# importar componentes del módulo PyAfipWs
from pyafipws.wsaa import WSAA
from pyafipws.wsfev1 import WSFEv1

# instanciar el componente para factura electrónica mercado interno
wsfev1 = WSFEv1()
wsfev1.LanzarExcepciones = True

# datos de conexión (cambiar URL para producción)
cache = None
wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
proxy = ""
wrapper = ""    # "pycurl" para usar proxy avanzado / propietarios
cacert = None   # "afip_ca_info.crt" para verificar canal seguro

# conectar al webservice de negocio
ok = wsfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)
if not ok:
    raise RuntimeError("Error WSFEv1: %s" % WSAA.Excepcion)

# autenticarse frente a AFIP (obtención de ticket de acceso):
cert = "reingart.crt"       # archivos a tramitar previamente ante AFIP 
clave = "reingart.key"      # (ver manual)
wsaa_url = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
ta = WSAA().Autenticar("wsfe", cert, clave, wsaa_url, debug=True)
if not ta:
    raise RuntimeError("Error WSAA: %s" % WSAA.Excepcion)

# establecer credenciales (token y sign) y cuit emisor:
wsfev1.SetTicketAcceso(ta)
wsfev1.Cuit = "20267565393"

# datos de la factura de prueba (encabezado):
tipo_cbte = 6
punto_vta = 4001
cbte_nro = long(wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta) or 0)
fecha = datetime.datetime.now().strftime("%Y%m%d")
concepto = 2
tipo_doc = 80
nro_doc = "30500010912"   # CUIT BNA
cbt_desde = cbte_nro + 1  # usar proximo numero de comprobante
cbt_hasta = cbte_nro + 1  # desde y hasta distintos solo lotes factura B
imp_total = "122.00"      # sumatoria total
imp_tot_conc = "0.00"     # importe total conceptos no gravado
imp_neto = "100.00"       # importe neto gravado (todas las alicuotas)
imp_iva = "21.00"         # importe total iva liquidado (idem)
imp_trib = "1.00"         # importe total otros conceptos
imp_op_ex = "0.00"        # importe total operaciones exentas
fecha_cbte = fecha
fecha_venc_pago = fecha
# Fechas del período del servicio facturado (solo si concepto != 1)
fecha_serv_desde = fecha
fecha_serv_hasta = fecha
moneda_id = 'PES'         # actualmente no se permite otra moneda
moneda_ctz = '1.000'

# inicializar la estructura de factura (interna)
wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
    cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
    imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
    fecha_serv_desde, fecha_serv_hasta, #--
    moneda_id, moneda_ctz)

# agregar comprobantes asociados (solo para Notas de Débito y Cŕedito)
if tipo_cbte not in (1, 6, 11):
    tipo = 1       # tipo de comprobante asociado
    pto_vta = 2    # punto de venta
    nro = 1234     # nro de comprobante asociado
    wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro)

# agregar otros impuestos (repetir por cada tributo diferente)
id = 99                              # tipo de tributo (ver tabla)
desc = 'Impuesto Municipal Matanza'  # descripción del tributo
base_imp = 100                       # base imponible
alic = 1                             # alicuota iva
importe = 1                          # importe liquidado del tributo
wsfev1.AgregarTributo(id, desc, base_imp, alic, importe)

# agregar subtotales por tasa de iva (repetir por cada alicuota):
id = 5              # 4: 10.5%, 5: 21%, 6: 27% (no enviar si es otra alicuota)
base_imp = 100      # neto gravado por esta alicuota
importe = 21        # importe de iva liquidado por esta alicuota
wsfev1.AgregarIva(id, base_imp, importe)

# llamar al webservice de AFIP para autorizar la factura y obtener CAE:
wsfev1.CAESolicitar()

# datos devueltos por AFIP:
print "Resultado", wsfev1.Resultado
print "Reproceso", wsfev1.Reproceso
print "CAE", wsfev1.CAE
print "Vencimiento", wsfev1.Vencimiento
print "Mensaje Error AFIP", wsfev1.ErrMsg
print "Mensaje Obs AFIP", wsfev1.Obs

# guardar mensajes xml (para depuración)
open("xmlrequest.xml","wb").write(wsfev1.XmlRequest)
open("xmlresponse.xml","wb").write(wsfev1.XmlResponse)

# ejemplo de obtención de atributos xml específicos
wsfev1.AnalizarXml("XmlResponse")
print wsfev1.ObtenerTagXml('CAE')
print wsfev1.ObtenerTagXml('Concepto')
print wsfev1.ObtenerTagXml('Obs',0,'Code')
print wsfev1.ObtenerTagXml('Obs',0,'Msg')


```

Al ejecutarlo se obtendrá un resultado similar al siguiente:

```
Resultado A
Reproceso 
CAE 64253188088810
Vencimiento 20140629
Mensaje Error AFIP 
Mensaje Obs AFIP 10063: Factura individual, DocTipo: 80, DocNro 27269434894 no se encuentra inscripto en condicion ACTIVA en el impuesto.
```

## Aclaraciones ##

Para instalarlo, simplemente bajar y descomprimir el codigo fuente de esta biblitoteca en una carpeta pyafipws. Para más información ver InstalacionCodigoFuente

Importante: debe tramitar los certificados y habilitar su CUIT para operar con los servidores de AFIP, tanto en pruebas (homologación) como en producción. Ver [manual](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#Certificados)

Por favor, no utilizar los comentarios de esta página para consultas de soporte técnico. Ver [foro público](http://groups.google.com/group/pyafipws) para más información