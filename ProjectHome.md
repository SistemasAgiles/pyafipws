<table width='100%' border='0'>
<tr><td width='30%'><a href='http://www.python.org/'><img src='http://www.python.org/static/community_logos/python-logo.png' alt='Python' border='0' align='left' /></a>
</td><td width='30%'><a href='http://www.pyafipws.com.ar/'><img src='http://www.pyafipws.com.ar/_/rsrc/1262297678232/config/app/images/customLogo/customLogo.gif?revision=1' align='center' border='0' alt='PyAfipWs' /></a>
</td><td width='30%'><a href='http://www.gnu.org/licenses/gpl.html'><img src='http://www.gnu.org/graphics/gplv3-127x51.png' alt='GPLv3' border='0' align='left' /></a>
</td>
<td><a href='https://github.com/reingart/pyafipws'><img src='https://s3.amazonaws.com/github/ribbons/forkme_right_red_aa0000.png' alt='Fork me on GitHub' border='0' /></a>
</td></tr>
</table>

**PyAfipWs** contienen módulos para acceder a los servicios webs de factura electronica de la AFIP (RG1956/05, RG1361/02, RG1345/02, RG2265/07, RG2289/07, RG2177/06, RG2485/08, RG2904/10, RG2926/10, RG3067/11, RG3536/13, RG3571/13, RG3668/14), liquidación y trazabilidad de granos, consulta de operaciones cambiaras, depositario fiel. También incluye soporte para código de operaciones de translado -remito electrónico- (ARBA), servicios web de trazabilidad de medicamentos (ANMAT), precursores químicos (SEDRONAR/RENPRE) y productos fitosanitarios/veterinarios (SENASA).

<a href='http://www.sistemasagiles.com.ar/trac/wiki/PyFactura'><img src='http://www.pyafipws.com.ar/_/rsrc/1402698702338/inicio/aplicativo_factura_electronica_06b_ubuntu.png?height=317&width=320' align='right' border='0' /></a>

For more information see **ProjectSummary**, [PyAr Magazine Article](http://revista.python.org.ar/2/en/html/pyafip.html) (in English) and related projects:
  * [PySimpleSoap](http://code.google.com/p/pysimplesoap/): the SOAP library developed to support this project
  * [PyFPDF](http://pyfpdf.googlecode.com): the PDF library ported and maintained from PHP to generate electronic invoices
  * [gui2py](http://gui2py.googlecode.com): GUI software development kit to design visual user interfaces (based on Pythoncard)

Source Code also available on [GitHub](https://github.com/reingart/pyafipws)

**New**: Integrated modules available for [OpenERP](https://github.com/reingart/openerp_pyafipws) and [Tryton](https://github.com/tryton-ar/account_invoice_ar), ask about other solutions for ERPs (SAP, MS Dinamics, etc.).

Además, se ha desarrollado una [interface COM](http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs) [simil OCX](http://www.sistemasagiles.com.ar/trac/wiki/OcxFacturaElectronica) para Windows y [librería](http://www.sistemasagiles.com.ar/trac/wiki/DllFacturaElectronica) [DLL (enlace dinámico)](http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs), compatible con otros lenguajes (_Visual Basic_, _Visual Fox Pro_, _Delphi_, _PHP_, _.Net_, _Java_, _ABAP_, C / C++, etc.) y herramientas multiplataforma (Linux y Windows) similar a [aplicativo SIAP/RECE](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#InterfaseporarchivosdetextosímilSIAP-RECE) por archivo de texto, tablas DBF (_dBase_, _Fox Pro_, _Clipper_, _Harbour_ etc.) o JSON (ver [factura\_electronica.php](https://code.google.com/p/pyafipws/source/browse/ejemplos/factura_electronica.php)) , incluyendo [PyFePDF](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#PyFEPDF:generadordePDFdefacturaselectrónicas) con soporte para generación de facturas en formato PDF y herramienta para consultar [Padron de Constribuyentes AFIP](http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP)

### Servicios web soportados: ###
  * [WSAA AFIP](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#ServicioWebdeAutenticaciónyAutorizaciónWSAA): autenticación y autorización
  * [WSFEv1 AFIP](http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs): factura electrónica - RG485 incluyendo [CAEA](http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaCAEAnticipado)
  * [WSMTXCA](http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaMTXCAService): factura electrónica con detalle - RG2904 incluyendo [CAEA](http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaCAEAnticipado)
  * [WSBFE AFIP](http://www.sistemasagiles.com.ar/trac/wiki/BonosFiscales): bono fiscal electrónico - RG2557
  * [WSFEXv1 AFIP](http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion): factura electrónica exportación - RG2758 y RG3066
  * [WSCTG AFIP](http://www.sistemasagiles.com.ar/trac/wiki/CodigoTrazabilidadGranos): código de trazabilidad de granos
  * [wDigDepFiel AFIP](http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#wDigDepFiel:DepositarioFiel): depositario fiel (aduana)
  * [WSCOC AFIP](http://www.sistemasagiles.com.ar/trac/wiki/ConsultaOperacionesCambiarias): consultas de operaciones de cambiarias (compras de divisas) RG3210
  * [WSLPG AFIP](http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos): Liquidación Electrónica Primaria de Granos RG3419/12 (**nuevo!**)
  * [WSCDC AFIP](http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes): Constatación de Comprobantes emitidos (CAI, CAE, CAEA) **nuevo!**
  * [COT ARBA](http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCotArba): remito electrónico (código de operaciones de translado)
  * [TrazaMed ANMAT](http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos): Programa Nacional de Trazabilidad de Medicamentos Disp.3683/11
  * [Traza  RENPRE](http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadPrecursoresQuimicos): Programa Nacional de Trazabilidad de Precursores Quimicos Res.900/13 **nuevo!**
  * [TrazaFito / TrazaVet SENASA](http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosFitosanitarios): Programa Nacional de Trazabilidad de Productos Agroquimicos Fitosanitarios / Veterinarios Res.369/13 **nuevo!**

También se ha desarrollado un aplicativo PyRece (ejecutable con interfase "visual") para windows/linux, que autoriza, genera PDF y envia los mails con facturas electrónicas (de manera libre y gratis). Ver PyFactura para aplicación visual simple para obtener CAE y generar PDF.

Se incluye soporte para el Web Service de Autorización y Autenticación (WSAA), Web Service de Factura Electrónica mercado interno (WSFE), Web Service de Bono Fiscal Electrónico (WSBFE) -RG2557 bienes de capital-, Web Service de Codigo de Trazabilidad de Granos (WSCTG), el Web Service de Factura Electrónica de Exportación (WSFEX) -RG2758/10- y los nuevos webservices de mercado interno (factura con y sin detalle, CAE y CAE Anticipado) -WSMTXCA y WSFEv1 según RG2904/10 y RG2926/10-

Ver http://www.pyafipws.com.ar para más información.

### Publicaciones y Presentaciones: ###

  * [Artículo](http://www.41jaiio.org.ar/sites/default/files/15_JSL_2012.pdf) (41JAIIO - JSL 2012 - ISSN: 1850-2857) y [Charla](http://www.41jaiio.org.ar/sites/default/files/ProgramaJSL.pdf) en las JAIIO 2012 (Jornadas Argentinas de Informática Organizadas por SADIO y celebrado en la Universidad de La Plata)
  * [Artículo](http://revista.python.org.ar/2/es/html/pyafip.html) Revista Python Entre Todos. Abril 2011. ISSN 1853-2071
  * Charla en la [CISL 2011](http://www.cisl.org.ar/). [Presentación](http://t.co/albZqNY) - [Video](http://t.co/tsRTnNg) (Conferencia Internacional de Software Libre, celebrada en la Biblioteca Nacional)
  * [Charla en Conferencia Python Argentina 2010](http://ar.pycon.org/2010/activity/accepted#451) (Córdoba, Universidad Siglo 21)
  * [Charla (r) en Conferencia Python Argentina 2009](http://ar.pycon.org/2009/conference/schedule/event/37/)
  * [Curso](http://www.clubdeprogramadores.com/cursos/CursoMuestra.php?Id=600) en la ACP 2010 y [Curso](http://www.clubdeprogramadores.com/cursos/CursoMuestra.php?Id=485) en la ACP 2009 (Materiales)
  * [Charla](http://www.conurbania.org/pagina/1248) en Conferencia Conurbania 2009
  * Charla (r) en Jornadas Regionales de Software Libre 2010 (San Luis)
  * [Taller](http://www.pyday.com.ar/catan2011) en PyDay González Catán 2011
  * [Reuniones de desarrollo](http://ar.pycon.org/2012/projects/index#29) en la Conferencia Python Argentina 2012 (Buenos Aires)


Software Libre, Código Abierto (Licencia [GPLv3](http://www.gnu.org/copyleft/gpl.html)).
  * Soporte comunitario gratuito sin cargo en el [Foro Público de Noticias/Consultas](https://groups.google.com/forum/#!forum/pyafipws)
  * Soporte comercial: [Sistemas Ágiles](http://www.sistemasagiles.com.ar/)

Ver [Instructivo Instalación desde el Código Fuente](https://code.google.com/p/pyafipws/wiki/InstalacionCodigoFuente) (homologación/producción)

&lt;wiki:gadget url="http://www.ohloh.net/p/322493/widgets/project\_basic\_stats.xml" height="220" border="1"/&gt;