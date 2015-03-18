Para documentación en español, ver:
http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
(full user manual - documentation)

For more information in Spanish see: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion



# Introduction #

WSFEX is the webservice to authorize foreign trade invoices according AFIP (Argentina "IRS") regulations.

This webservice allows to authorize an invoice (i.e. get the CAE: Electronic Autorization Code) so it can be sent to the customer.

Invoice Class:
  * E: sales to foreign customers (Exports)

AFIP General Resolutions:
  * RG2485: General Regime
  * RG2758: Foreign trade (Export operations)

Webservice:
  * Current: WSFEX (a.k.a. version 0) available until 31/12/2011
  * Future: WSFEXv1 (version 1, minor changes to WSFEX)

PyAfipWs Interface options:
  * COM Interface (windows only): CreateObject("WSFEX")
  * Command-line communication tool: RECEX.EXE
  * Python module: wsfex.py

Current Installer:
  * Stable: [all-in-one installer](http://pyafipws.googlecode.com/files/instalador-PyAfipWs-1.25c-homo.exe) (recommended)
  * Development: (new version not yet released)

Installers are for evaluation purposes only (testing - homologation).
For production, consult our [Commercial Support](http://www.sistemasagiles.com.ar) or see InstalacionCodigoFuente (Source Code Installation Instructions)

# Details #

Most modern programming languages in windows support COM Automation  (a.k.a. Component Object Model, ActiveX DLL, similar to OCX controls) via CreateObject or similar function, and this interface exposes WSAA and WSFEv1 objects to be used directly from legacy programs.

Some known supported programming languages so far:
  * Visual Basic Classic (5,6)
  * Visual Basic .Net
  * Visual Basic For Applications (MS Access, MS Excel, et. al.)
  * Visual Fox Pro
  * Delphi
  * ABAP (SAP)
  * Fujitsu NetCobol
  * Powerbuilder
  * X++ (Microsoft Dynamics)
  * Genexus

If your programming language doesn't support COM, the interface has a Command Line Tool called RECE1 to perform invoice authorization using text files or DBF tables (see bellow).

## Visual Basic (5/6) COM Example ##

The following code is a detailed example to explain main features and recommended process and data needed to authorize a valid electronic invoice:

```
' Simple example COM Interface with new WSFEX AFIP webservice
' As of RG758 (Foreign Trade - Export Operations)
' For a complete workflow see WSFEv1 Example
' 2010 (C) Mariano Reingart <reingart@gmail.com>
' License: GPLv3

' Create an internal invoice (do not call webservice yet):
ok = WSFEX.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, _
            imp_total, tipo_expo, permiso_existente, dst_cmp, _
            cliente, cuit_pais_cliente, domicilio_cliente, _
            id_impositivo, moneda_id, moneda_ctz, _
            obs_comerciales, obs, forma_pago, incoterms, _
            idioma_cbte)
    
' Add an invoice item:
ok = WSFEX.AgregarItem(codigo, ds, qty, umed, precio, imp_total)

' Add a export permission 
ok = WSFEX.AgregarPermiso(id_permiso, pais_dst)
        
' Add and related invoice 
ok = WSFEX.AgregarCmpAsoc(tipo_cbte_asoc, punto_vta_asoc, cbte_nro_asoc)

' Call WebService to get the CAE
cae = WSFEX.Authorize(id)
```

## RECEX Command Line tool ##

RECEX is our tool that using text files for legacy programming languages in a simplified way, no user interaction is required, with the advantage that communication is done instantaneously using webservices, so CAE number is returned immediately, no further process is needed, and can be done in background automatically.

### RECEX Command line parameters ###
  * /ayuda: show help
  * /prueba: generate a test invoice and get CAE for it, saving input and ouput files with sample values. DO NOT USE IN PRODUCTION.
  * /ult: ask for invoice type and sale point, returns the last invoice number registered at AFIP
  * /dummy: queries AFIP server status (the three servers should return OK if they are working properly)
  * /debug: show extensive debug messages y and ask for confirmation prior sending the data to AFIP servers
  * /formato: show input/output file format
  * /get: recover previously authorized invoice, returns all informed data if available.
  * /xml: save XML request and response messages

### RECEX Configuration File (rece.ini) ###

Before start using RECE1 tool, you must generate your private key and certificate files, and then edit the file RECE.INI in the interface folder (i.e. C:\WSFEv1):

Section [WSAA](WSAA.md):
  * CERT: path to the certificate file ()
  * PRIVATEKEY: path to the private key file
  * CUIT: CUIT of the company that generates the invoices
  * URL: location of the webservice (uncomment removing # to use in production, if not, it connects to testing servers "homologacion")

Section [WSFEX](WSFEX.md):
  * ENTRADA: path to the input text file
  * SALIDA: path to the ouput text file
  * URL: location of the webservice (uncomment removing # to use in production, if not, it connects to testing servers "homologacion")

Sample configuration file (minimal):
```
[WSAA]
CERT=homo.crt
PRIVATEKEY=homo.key
##URL=https://wsaa.afip.gov.ar/ws/services/LoginCms

[WSFEX]
CUIT=30000000000
ENTRADA=entrada.txt
SALIDA=salida.txt
##URL=https://servicios1.afip.gov.ar/wsfex/service.asmx?WSDL
```

### RECEX Usage ###
Sample usage (create a test invoice, show debug messages):
```
C:\PYAFIPWS>RECEX.EXE /debug /prueba
wsaa_url https://wsaahomo.afip.gov.ar/ws/services/LoginCms
wsfex_url https://wswhomo.afip.gov.ar/wsfex/service.asmx
Imp_total='250.0'
Incoterms='FOB'
Tipo_cbte='19'
Domicilio_cliente='Rua 76 km 34.5 Alagoas'
Moneda_ctz='3.875'
Id_impositivo='PJ54482221-l'
Fecha_cbte='20110616'
Cbte_nro='38'
Punto_vta='3'
Forma_pago='30 dias'
Obs='Sin observaciones'
Items='[{'Item': {'Pro_precio_uni': 125.0, 'Pro_umed': '7', 'Pro_ds': u'Producto
 Tipo 1 Exportacion MERCOSUR ISO 9001', 'Pro_total_item': 125.0, 'Pro_qty': 1.0,
 'Pro_codigo': u'PRO1'}}, {'Item': {'Pro_precio_uni': 125.0, 'Pro_umed': '7', 'P
ro_ds': u'Producto Tipo 2 Exportacion MERCOSUR ISO 9001', 'Pro_total_item': 125.
0, 'Pro_qty': 1.0, 'Pro_codigo': u'PRO2'}}]'
Tipo_expo='1'
Idioma_cbte='1'
Dst_cmp='203'
Permisos='[{'Permiso': {'Dst_merc': '225', 'Id_permiso': u'99999AAXX999999A'}}]'

Cuit_pais_cliente='50000000016'
Moneda_Id='DOL'
Permiso_existente='S'
Cliente='Joao Da Silva'
Obs_comerciales='Observaciones comerciales'
id: 99000000001257
Facturar?S
ID: 99000000001257 CAE: 61243000517776 Obs:  Reproceso: N
```

Normal usage (don't show debug messages nor make test invoice, but save XML files):
```
C:\WSFEv1>RECEX.EXE /xml
ID: 99000000001257 CAE: 61243000517776 Obs:  Reproceso: S
```

Usage to query last invoice informed to AFIP and recover previously sent invoice data (Tipo de Comprobante: invoice type, Punto de Venta: point of sale, Ultimo numero: last invoice number, Fecha: date):
```
C:\WSFEv1>RECEX.EXE /ult
Consultar ultimo numero:
Tipo de comprobante: 19
Punto de venta: 3
Ultimo numero:  38
Fecha:  20110616

C:\WSFEv1>RECEX.EXE  /get
Recuperar comprobante:
Tipo de comprobante: 19
Punto de venta: 3
Numero de comprobante: 38
imp_total = 250
fch_cbte = 20110616
fch_venc_cae = 20110626
cuit = 50000000016
obs = Sin observaciones
cae = 61243000517776
```

## RECEX File Format ##

Input and output files have the same format, only returned fields are completed in the output file (cae, fch\_venc\_cae, resultado, errmsg, etc.)

Important: you must check current format with /formato parameter because you can have a another version with different field structure.

Records must be separated by line feed (LF) and/or carriage return (CR) depending the operating system convention.
Each record have a type in the first character (0: Invoice Header, 1: Invoice item detail, 2: Export license - export permit, 3: Related Invoices):

### Invoice Header record ###
  * Field: tipo\_reg  (record type)            Position:   1 Lenght:    1 Type: Numeric Decimals:
  * Field: fecha\_cbte (invoice date)           Position:   2 Lenght:    8 Type: AlphaNumeric Decimals:
  * Field: tipo\_cbte (invoice type)            Position:  10 Lenght:    2 Type: Numeric Decimals:
  * Field: punto\_vta (point of sale)           Position:  12 Lenght:    4 Type: Numeric Decimals:
  * Field: cbte\_nro (invoice number)           Position:  16 Lenght:    8 Type: Numeric Decimals:
  * Field: tipo\_expo (export type)           Position:  24 Lenght:    1 Type: Numeric Decimals:
  * Field: permiso\_existente (has export permit/license, 'S': Yes, 'N': No, '': not applicable)   Position:  25 Lenght:    1 Type: AlphaNumeric Decimals:
  * Field: dst\_cmp (destination country code)             Position:  26 Lenght:    3 Type: Numeric Decimals:
  * Field: cliente (customer name)             Position:  29 Lenght:  200 Type: AlphaNumeric Decimals:
  * Field: cuit\_pais\_cliente (customer country CUIT)    Position: 229 Lenght:   11 Type: Numeric Decimals:
  * Field: domicilio\_cliente (customer address)   Position: 240 Lenght:  300 Type: AlphaNumeric Decimals:
  * Field: id\_impositivo (customer tax id)       Position: 540 Lenght:   50 Type: AlphaNumeric Decimals:
  * Field: imp\_total (total amount)           Position: 590 Lenght:   15 Type: Importe Decimals: 3
  * Field: moneda\_id (currency code)           Position: 605 Lenght:    3 Type: AlphaNumeric Decimals:
  * Field: moneda\_ctz (currency quotation)         Position: 608 Lenght:   10 Type: Importe Decimals: 6
  * Field: obs\_comerciales (commercial remarks)     Position: 618 Lenght: 1000 Type: AlphaNumeric Decimals:
  * Field: obs (general remarks / invoice description)                 Position: 1618 Lenght: 1000 Type: AlphaNumeric Decimals:
  * Field: forma\_pago (payment method description)          Position: 2618 Lenght:   50 Type: AlphaNumeric Decimals:
  * Field: incoterms (incoterms code)           Position: 2668 Lenght:    3 Type: AlphaNumeric Decimals:
  * Field: incoterms\_ds (incoterms description)         Position: 2671 Lenght:   20 Type: AlphaNumeric Decimals:
  * Field: idioma\_cbte (invoice language)          Position: 2691 Lenght:    1 Type: AlphaNumeric Decimals:
  * Field: cae                  Position: 2692 Lenght:   14 Type: Numeric Decimals:
  * Field: fecha\_vto (due date)           Position: 2706 Lenght:    8 Type: AlphaNumeric Decimals:
  * Field: resultado (result, A: Aproved, R: rejected)           Position: 2714 Lenght:    1 Type: AlphaNumeric Decimals:
  * Field: reproceso  (reprocess previos sent invoice, blank: not needed, S: succed, N: fail, check data)            Position: 2715 Lenght:    1 Type: AlphaNumeric Decimals:
  * Field: motivos\_obs (observation message)          Position: 2716 Lenght:   40 Type: AlphaNumeric Decimals:
  * Field: id (invoice unique identification number)                  Position: 2756 Lenght:   15 Type: Numeric Decimals:
  * Field: fch\_venc\_cae (cae due date)        Position: 2771 Lenght:    8 Type: AlphaNumeric Decimals:

### Invoice line item detail (Detalle) ###

  * Field: tipo\_reg (record type, value: 1)            Position:   1 Lenght:    1 Type: Numeric Decimals:
  * Field: codigo (product code)               Position:   2 Lenght:   30 Type: AlphaNumeric Decimals:
  * Field: qty (quantity)                 Position:  32 Lenght:   12 Type: Importe Decimals:
  * Field: umed (measure unit code, see table)                Position:  44 Lenght:    2 Type: Numeric Decimals:
  * Field: precio (product price)             Position:  46 Lenght:   12 Type: Importe Decimals: 3
  * Field: imp\_total (total amount = qty\*price)           Position:  58 Lenght:   14 Type: Importe Decimals: 3
  * Field: ds (product description)                   Position:  72 Lenght: 4000 Type: AlphaNumeric Decimals:

### Export licence/permit (Permisos de Exportación) ###

  * Field: tipo\_reg (record type, value: 2)             Position:   1 Lenght:    1 Type: Numeric Decimals:
  * Field: id\_permiso (export licence or permit identification number)           Position:   2 Lenght:   16 Type: AlphaNumeric Decimals:
  * Field: dst\_merc (destination country code)            Position:  18 Lenght:    3 Type: Numeric Decimals:

### Related invoice records (Comprobante Asociado) ###
  * Field: tipo\_reg (record type, value: 3)             Position:   1 Lenght:    1 Type: Numeric Decimals: Value: 3 (always)
  * Field: tipo (invoice type, see table) Position:   2 Lenght:    3 Type: Numeric Decimals:
  * Field: pto\_vta (sale point number)             Position:   5 Lenght:    4 Type: Numeric Decimals:
  * Field: nro (invoice number)                Position:   9 Lenght:    8 Type: Numeric Decimals:

## WSFEX/RECEX Parameter Tables ##

This webservice is parametrized with the following tables:

### Currencies (Monedas) ###

|Id (currency\_id)|Desc (description)|FchDesde-FchHasta (applicable dates from-to)|
|:----------------|:-----------------|:-------------------------------------------|
|PES|Pesos Argentinos (ARS)|(20090403-NULL)|
|DOL|Dólar Estadounidense (USD)|(20090403-NULL)|
|002|Dólar Libre EEUU (USD - free)|(20090416-NULL)|
|007|Florines Holandeses|(20090403-NULL)|
|010|Pesos Mejicanos (MXN)|(20090403-NULL)|
|011|Pesos Uruguayos (UYP)|(20090403-NULL)|
|014|Coronas Danesas (DKK)|(20090403-NULL)|
|015|Coronas Noruegas|(20090403-NULL)|
|016|Coronas Suecas|(20090403-NULL)|
|018|Dólar Canadiense (CAD)|(20090403-NULL)|
|019|Yens (JPY)|(20090403-NULL)|
|021|Libra Esterlina (GBP)|(20090403-NULL)|
|023|Bolívar Venezolano (VEB)|(20090403-NULL)|
|024|Corona Checa|(20090403-NULL)|
|025|Dinar Yugoslavo|(20090403-NULL)|
|026|Dólar Australiano (AUD)|(20090403-NULL)|
|027|Dracma Griego (GRD)|(20090403-NULL)|
|028|Florín (Antillas Holandesas)|(20090403-NULL)|
|029|Güaraní|(20090403-NULL)|
|031|Peso Boliviano (PYG)|(20090403-NULL)|
|032|Peso Colombiano (COP)|(20090403-NULL)|
|033|Peso Chileno (CLP)|(20090403-NULL)|
|034|Rand Sudafricano|(20090403-NULL)|
|036|Sucre Ecuatoriano|(20090403-NULL)|
|051|Dólar de Hong Kong (HKD)|(20090403-NULL)|
|052|Dólar de Singapur (SGD)|(20090403-NULL)|
|053|Dólar de Jamaica|(20090403-NULL)|
|054|Dólar de Taiwan (TWD)|(20090403-NULL)|
|055|Quetzal Guatemalteco|(20090403-NULL)|
|056|Forint (Hungría)|(20090403-NULL)|
|057|Baht (Tailandia)|(20090403-NULL)|
|059|Dinar Kuwaiti|(20090403-NULL)|
|012|Real (BRL)|(20090403-NULL)|
|030|Shekel (Israel)|(20090403-NULL)|
|035|Nuevo Sol Peruano|(20090403-NULL)|
|060|Euro (ECU)|(20090403-NULL)|
|040|Lei Rumano|(20090415-NULL)|
|042|Peso Dominicano|(20090415-NULL)|
|043|Balboas Panameñas|(20090415-NULL)|
|044|Córdoba Nicaragüense|(20090415-NULL)|
|045|Dirham Marroquí|(20090415-NULL)|
|046|Libra Egipcia|(20090415-NULL)|
|047|Riyal Saudita|(20090415-NULL)|
|061|Zloty Polaco|(20090415-NULL)|
|062|Rupia Hindú|(20090415-NULL)|
|063|Lempira Hondureña|(20090415-NULL)|
|064|Yuan (Rep. Pop. China) (RMB)|(20090415-NULL)|
|009|Franco Suizo (CHF)|(20091110-NULL)|
|041|Derechos Especiales de Giro|(20100125-NULL)|
|049|Gramos de Oro Fino|(20100125-NULL)|

### Invoice Types (Tipos Comprobante) ###
|19|Facturas de Exportación E (Export Invoice E) |
|:-|:---------------------------------------------|
|20|Nota de Débito por Operaciones con el Exterior E (Export Debit Note E)|
|21|Nota de Crédito por Operaciones con el Exterior (Export Credit Note E)|

### Export Types (Tipos Exportación) ###
|1|Exportación definitiva de Bienes (Goods -products- final export)|
|:|:----------------------------------------------------------------|
|2 |Servicios (Services)|
|4 |Otros (Other - "both producs and services")|

### Invoice Language (Idiomas) ###
|1|Español (Spanish)|
|:|:-----------------|
|2 |Inglés (English)|
|3 |Portugués (Portuguese -brazilian-)|

### Measurement Units (Unidades de medida) ###
|41|miligramos (mg)|
|:-|:--------------|
|14|gramos (g)|
|1 |kilogramos (kg)|
|29|toneladas (tn)|
|10|quilates (ct) |
|47|mililitros (ml)|
|5 |litros (l)|
|27|cm cúbicos (cm3)|
|15|milimetros (mm)|
|20|centímetros (cm)|
|17|kilómetros (km)|
|7 |unidades (unit - u)|
|8 |pares (pairs)|
|9 |docenas (dozens)|
|11|millares|
|96|packs|
|97|hormas|
|2 |metros (m)|
|3 |metros cuadrados (m2)|
|4 |metros cúbicos (m3)|
|6 |1000 kWh|
|16|mm cúbicos (mm3)|
|18|hectolitros (hl)|
|25|jgo. pqt. mazo naipes (deck of cards)|
|30|dam cúbicos|
|31|hm cúbicos (hm3)|
|32|km cúbicos (km3)|
|33|microgramos (mg)|
|34|nanogramos (ng)|
|35|picogramos (pg)|
|48|curie|
|49|milicurie|
|50|microcurie|
|51|uiacthor|
|52|muiacthor|
|53|kg base|
|54|gruesa|
|61|kg bruto|
|62|uiactant|
|63|muiactant|
|64|uiactig|
|65|muiactig|
|66|kg activo|
|67|gramo activo|
|68|gramo base|
|0 |description (no amount) **WSFEXv1** |
|97|seña/anticipo (cash advance, negative amounts) **WSFEXv1**|
|98|otras unidades (other units) **WSFEXv1**|
|99|bonificación (discount, negative amounts) **WSFEXv1**|

### INCOTERMs ###
|EXW|EXW|
|:--|:--|
|FCA|FCA|
|FAS|FAS|
|FOB|FOB|
|CFR|CFR|
|CIF|CIF|
|CPT|CPT|
|CIP|CIP|
|DAF|DAF|
|DES|DES|
|DEQ|DEQ|
|DDU|DDU|
|DDP|DDP|

### Destination Country (Pais Destino) ###
|101|BURKINA FASO|
|:--|:-----------|
|102|ARGELIA|
|103|BOTSWANA|
|104|BURUNDI|
|105|CAMERUN|
|107|REP. CENTROAFRICANA.|
|108|CONGO|
|109|REP.DEMOCRAT.DEL CONGO EX ZAIRE|
|110|COSTA DE MARFIL|
|111|CHAD|
|112|BENIN|
|113|EGIPTO|
|115|GABON|
|116|GAMBIA|
|117|GHANA|
|118|GUINEA|
|119|GUINEA ECUATORIAL|
|120|KENYA|
|121|LESOTHO|
|122|LIBERIA|
|123|LIBIA|
|124|MADAGASCAR|
|125|MALAWI|
|126|MALI|
|127|MARRUECOS|
|128|MAURICIO,ISLAS|
|129|MAURITANIA|
|130|NIGER|
|131|NIGERIA|
|132|ZIMBABWE|
|133|RWANDA|
|134|SENEGAL|
|135|SIERRA LEONA|
|136|SOMALIA|
|137|SWAZILANDIA|
|138|SUDAN|
|139|TANZANIA|
|140|TOGO|
|141|TUNEZ|
|142|UGANDA|
|144|ZAMBIA|
|145|TERRIT.VINCULADOS AL R UNIDO|
|146|TERRIT.VINCULADOS A ESPAÑA|
|147|TERRIT.VINCULADOS A FRANCIA|
|149|ANGOLA|
|150|CABO VERDE|
|151|MOZAMBIQUE|
|152|SEYCHELLES|
|153|DJIBOUTI|
|155|COMORAS|
|156|GUINEA BISSAU|
|157|STO.TOME Y PRINCIPE|
|158|NAMIBIA|
|159|SUDAFRICA|
|160|ERITREA|
|161|ETIOPIA|
|197|RESTO (AFRICA)|
|198|INDETERMINADO (AFRICA)|
|200|ARGENTINA|
|201|BARBADOS|
|202|BOLIVIA|
|203|BRASIL|
|204|CANADA|
|205|COLOMBIA|
|206|COSTA RICA|
|207|CUBA|
|208|CHILE|
|209|REPÚBLICA DOMINICANA|
|210|ECUADOR|
|211|EL SALVADOR|
|212|ESTADOS UNIDOS|
|213|GUATEMALA|
|214|GUYANA|
|215|HAITI|
|216|HONDURAS|
|217|JAMAICA|
|218|MEXICO|
|219|NICARAGUA|
|220|PANAMA|
|221|PARAGUAY|
|222|PERU|
|223|PUERTO RICO|
|224|TRINIDAD Y TOBAGO|
|225|URUGUAY|
|226|VENEZUELA|
|227|TERRIT.VINCULADO AL R.UNIDO|
|228|TER.VINCULADOS A DINAMARCA|
|229|TERRIT.VINCULADOS A FRANCIA AMERIC.|
|230|TERRIT. HOLANDESES|
|231|TER.VINCULADOS A ESTADOS UNIDOS|
|232|SURINAME|
|233|DOMINICA|
|234|SANTA LUCIA|
|235|SAN VICENTE Y LAS GRANADINAS|
|236|BELICE|
|237|ANTIGUA Y BARBUDA|
|238|S.CRISTOBAL Y NEVIS|
|239|BAHAMAS|
|240|GRENADA|
|241|ANTILLAS HOLANDESAS|
|250|AAE Tierra del Fuego - ARGENTINA|
|251|ZF La Plata - ARGENTINA|
|252|ZF Justo Daract - ARGENTINA|
|253|ZF Río Gallegos - ARGENTINA|
|254|Islas Malvinas - ARGENTINA|
|255|ZF Tucumán - ARGENTINA|
|256|ZF Córdoba - ARGENTINA|
|257|ZF Mendoza - ARGENTINA|
|258|ZF General Pico - ARGENTINA|
|259|ZF Comodoro Rivadavia - ARGENTINA|
|260|ZF Iquique|
|261|ZF Punta Arenas|
|262|ZF Salta - ARGENTINA|
|263|ZF Paso de los Libres - ARGENTINA|
|264|ZF Puerto Iguazú - ARGENTINA|
|265|SECTOR ANTARTICO ARG.|
|270|ZF Colón - REPÚBLICA DE PANAMÁ|
|271|ZF Winner (Sta. C. de la Sierra) - BOLIVIA|
|280|ZF Colonia - URUGUAY|
|281|ZF Florida - URUGUAY|
|282|ZF Libertad - URUGUAY|
|283|ZF Zonamerica - URUGUAY|
|284|ZF Nueva Helvecia - URUGUAY|
|285|ZF Nueva Palmira - URUGUAY|
|286|ZF Río Negro - URUGUAY|
|287|ZF Rivera - URUGUAY|
|288|ZF San José - URUGUAY|
|291|ZF Manaos - BRASIL|
|295|MAR ARG ZONA ECO.EX|
|296|RIOS ARG NAVEG INTER|
|297|RESTO AMERICA|
|298|INDETERMINADO (AMERICA)|
|301|AFGANISTAN|
|302|ARABIA SAUDITA|
|303|BAHREIN|
|304|MYANMAR (EX-BIRMANIA)|
|305|BUTAN|
|306|CAMBODYA (EX-KAMPUCHE)|
|307|SRI LANKA|
|308|COREA DEMOCRATICA|
|309|COREA REPUBLICANA|
|310|CHINA|
|312|FILIPINAS|
|313|TAIWAN|
|315|INDIA|
|316|INDONESIA|
|317|IRAK|
|318|IRAN|
|319|ISRAEL|
|320|JAPON|
|321|JORDANIA|
|322|QATAR|
|323|KUWAIT|
|324|LAOS|
|325|LIBANO|
|326|MALASIA|
|327|MALDIVAS ISLAS|
|328|OMAN|
|329|MONGOLIA|
|330|NEPAL|
|331|EMIRATOS ARABES UNIDOS|
|332|PAKISTÁN|
|333|SINGAPUR|
|334|SIRIA|
|335|THAILANDIA|
|337|VIETNAM|
|341|HONG KONG|
|344|MACAO|
|345|BANGLADESH|
|346|BRUNEI|
|348|REPUBLICA DE YEMEN|
|349|ARMENIA|
|350|AZERBAIJAN|
|351|GEORGIA|
|352|KAZAJSTAN|
|353|KIRGUIZISTAN|
|354|TAYIKISTAN|
|355|TURKMENISTAN|
|356|UZBEKISTAN|
|357|TERR. AU. PALESTINOS|
|397|RESTO DE ASIA|
|398|INDET.(ASIA)|
|401|ALBANIA|
|404|ANDORRA|
|405|AUSTRIA|
|406|BELGICA|
|407|BULGARIA|
|409|DINAMARCA|
|410|ESPAÑA|
|411|FINLANDIA|
|412|FRANCIA|
|413|GRECIA|
|414|HUNGRIA|
|415|IRLANDA|
|416|ISLANDIA|
|417|ITALIA|
|418|LIECHTENSTEIN|
|419|LUXEMBURGO|
|420|MALTA|
|421|MONACO|
|422|NORUEGA|
|423|PAISES BAJOS|
|424|POLONIA|
|425|PORTUGAL|
|426|REINO UNIDO|
|427|RUMANIA|
|428|SAN MARINO|
|429|SUECIA|
|430|SUIZA|
|431|VATICANO(SANTA SEDE)|
|433|POS.BRIT.(EUROPA)|
|435|CHIPRE|
|436|TURQUIA|
|438|ALEMANIA,REP.FED.|
|439|BIELORRUSIA|
|440|ESTONIA|
|441|LETONIA|
|442|LITUANIA|
|443|MOLDAVIA|
|444|RUSIA|
|445|UCRANIA|
|446|BOSNIA HERZEGOVINA|
|447|CROACIA|
|448|ESLOVAQUIA|
|449|ESLOVENIA|
|450|MACEDONIA|
|451|REP. CHECA|
|453|MONTENEGRO|
|454|SERBIA|
|497|RESTO EUROPA|
|498|INDET.(EUROPA)|
|501|AUSTRALIA|
|503|NAURU|
|504|NUEVA ZELANDIA|
|505|VANATU|
|506|SAMOA OCCIDENTAL|
|507|TERRITORIO VINCULADOS A AUSTRALIA|
|508|TERRITORIOS VINCULADOS AL R. UNIDO|
|509|TERRITORIOS VINCULADOS A FRANCIA|
|510|TER VINCULADOS A NUEVA. ZELANDA|
|511|TER. VINCULADOS A ESTADOS UNIDOS|
|512|FIJI, ISLAS|
|513|PAPUA NUEVA GUINEA|
|514|KIRIBATI, ISLAS|
|515|MICRONESIA,EST.FEDER|
|516|PALAU|
|517|TUVALU|
|518|SALOMON,ISLAS|
|519|TONGA|
|520|MARSHALL,ISLAS|
|521|MARIANAS,ISLAS|
|597|RESTO OCEANIA|
|598|INDET.(OCEANIA)|
|997|RESTO CONTINENTE|
|998|INDET.(CONTINENTE)|

### Destination Country CUIT (CUIT Pais Destino) ###
|50000000016|URUGUAY - Persona Física|
|:----------|:------------------------|
|50000000024|PARAGUAY - Persona Física|
|50000000032|CHILE - Persona Física|
|50000000040|BOLIVIA - Persona Física|
|50000000059|BRASIL - Persona Física|
|50000001012|BURKINA FASO - Persona Física|
|50000001020|ARGELIA - Persona Física|
|50000001039|BOTSWANA - Persona Física|
|50000001047|BURUNDI - Persona Física|
|50000001055|CAMERUN - Persona Física|
|50000001071|CENTRO AFRICANO, REP. - Persona Física|
|50000001101|COSTA DE MARFIL - Persona Física|
|50000001136|EGIPTO - Persona Física|
|50000001144|ETIOPIA - Persona Física|
|50000001152|GABON - Persona Física|
|50000001160|GAMBIA - Persona Física|
|50000001179|GHANA - Persona Física|
|50000001187|GUINEA - Persona Física|
|50000001195|GUINEA ECUATORIAL - Persona Física|
|50000001209|KENIA - Persona Física|
|50000001217|LESOTHO - Persona Física|
|50000001225|REPUBLICA DE LIBERIA (Estado independiente) - Persona Física|
|50000001233|LIBIA - Persona Física|
|50000001241|MADAGASCAR - Persona Física|
|50000001276|MARRUECOS - Persona Física|
|50000001284|REPUBLICA DE MAURICIO - Persona Física|
|50000001292|MAURITANIA - Persona Física|
|50000001306|NIGER - Persona Física|
|50000001314|NIGERIA - Persona Física|
|50000001322|ZIMBABWE - Persona Física|
|50000001330|RUANDA - Persona Física|
|50000001349|SENEGAL - Persona Física|
|50000001357|SIERRA LEONA - Persona Física|
|50000001365|SOMALIA - Persona Física|
|50000001373|REINO DE SWAZILANDIA (Estado independiente) - Persona Física|
|50000001381|SUDAN - Persona Física|
|50000001403|TOGO - Persona Física|
|50000001411|REPUBLICA TUNECINA - Persona Física|
|50000001446|ZAMBIA - Persona Física|
|50000001454|POS.BRITANICA (AFRICA) - Persona Física|
|50000001462|POS.ESPAÑOLA (AFRICA) - Persona Física|
|50000001470|POS.FRANCESA (AFRICA) - Persona Física|
|50000001489|POS.PORTUGUESA (AFRICA) - Persona Física|
|50000001497|REPUBLICA DE ANGOLA - Persona Física|
|50000001500|REPUBLICA DE CABO VERDE (Estado independiente) - Persona Física|
|50000001519|MOZAMBIQUE - Persona Física|
|50000001527|CONGO REP.POPULAR - Persona Física|
|50000001535|CHAD - Persona Física|
|50000001543|MALAWI - Persona Física|
|50000001551|TANZANIA - Persona Física|
|50000001586|COSTA RICA - Persona Física|
|50000001616|ZAIRE - Persona Física|
|50000001624|BENIN - Persona Física|
|50000001632|MALI - Persona Física|
|50000001705|UGANDA - Persona Física|
|50000001713|SUDAFRICA, REP. DE - Persona Física|
|50000001810|REPUBLICA DE SEYCHELLES (Estado independiente) - Persona Física|
|50000001829|SANTO TOME Y PRINCIPE - Persona Física|
|50000001837|NAMIBIA - Persona Física|
|50000001845|GUINEA BISSAU - Persona Física|
|50000001853|ERITREA - Persona Física|
|50000001861|REPUBLICA DE DJIBUTI (Estado independiente) - Persona Física|
|50000001896|COMORAS - Persona Física|
|50000001985|INDETERMINADO (AFRICA) - Persona Física|
|50000002019|BARBADOS (Estado independiente) - Persona Física|
|50000002043|CANADA - Persona Física|
|50000002051|COLOMBIA - Persona Física|
|50000002094|DOMINICANA, REPUBLICA - Persona Física|
|50000002116|EL SALVADOR - Persona Física|
|50000002124|ESTADOS UNIDOS - Persona Física|
|50000002132|GUATEMALA - Persona Física|
|50000002140|REPUBLICA COOPERATIVA DE GUYANA (Estado independiente) - Persona Física|
|50000002159|HAITI - Persona Física|
|50000002167|HONDURAS - Persona Física|
|50000002175|JAMAICA - Persona Física|
|50000002183|MEXICO - Persona Física|
|50000002191|NICARAGUA - Persona Física|
|50000002205|REPUBLICA DE PANAMA (Estado independiente) - Persona Física|
|50000002213|ESTADO LIBRE ASOCIADO DE PUERTO RICO (Estado asoc. a EEUU) - Persona Física|
|50000002221|PERU - Persona Física|
|50000002256|ANTIGUA Y BARBUDA (Estado independiente) - Persona Física|
|50000002264|VENEZUELA - Persona Física|
|50000002272|POS.BRITANICA (AMERICA) - Persona Física|
|50000002280|POS.DANESA (AMERICA) - Persona Física|
|50000002299|POS.FRANCESA (AMERICA) - Persona Física|
|50000002302|POS.PAISES BAJOS (AMERICA) - Persona Física|
|50000002310|POS.E.E.U.U. (AMERICA) - Persona Física|
|50000002329|SURINAME - Persona Física|
|50000002337|EL COMMONWEALTH DE DOMINICA (Estado Asociado) - Persona Física|
|50000002345|SANTA LUCIA - Persona Física|
|50000002353|SAN VICENTE Y LAS GRANADINAS (Estado independiente) - Persona Física|
|50000002361|BELICE (Estado independiente) - Persona Física|
|50000002396|CUBA - Persona Física|
|50000002426|ECUADOR - Persona Física|
|50000002434|REPUBLICA DE TRINIDAD Y TOBAGO - Persona Física|
|50000002825|BUTAN - Persona Física|
|50000002841|MYANMAR (EX BIRMANIA) - Persona Física|
|50000002876|ISRAEL - Persona Física|
|50000002882|ESTADO ASOCIADO DE GRANADA (Estado independiente) - Persona Física|
|50000002892|FEDERACION DE SAN CRISTOBAL (Islas Saint Kitts and Nevis) - Persona Física|
|50000002906|COMUNIDAD DE LAS BAHAMAS (Estado independiente) - Persona Física|
|50000002914|TAILANDIA - Persona Física|
|50000002922|INDETERMINADO (AMERICA) - Persona Física|
|50000002930|IRAN - Persona Física|
|50000002981|ESTADO DE QATAR (Estado independiente) - Persona Física|
|50000003007|REINO HACHEMITA DE JORDANIA - Persona Física|
|50000003015|AFGANISTAN - Persona Física|
|50000003023|ARABIA SAUDITA - Persona Física|
|50000003031|ESTADO DE BAHREIN (Estado independiente) - Persona Física|
|50000003066|CAMBOYA (EX KAMPUCHEA) - Persona Física|
|50000003074|REPUBLICA DEMOCRATICA SOCIALISTA DE SRI LANKA - Persona Física|
|50000003082|COREA DEMOCRATICA  - Persona Física|
|50000003090|COREA REPUBLICANA - Persona Física|
|50000003104|CHINA REP.POPULAR - Persona Física|
|50000003112|REPUBLICA DE CHIPRE (Estado independiente) - Persona Física|
|50000003120|FILIPINAS - Persona Física|
|50000003139|TAIWAN - Persona Física|
|50000003147|GAZA - Persona Física|
|50000003155|INDIA - Persona Física|
|50000003163|INDONESIA - Persona Física|
|50000003171|IRAK - Persona Física|
|50000003201|JAPON - Persona Física|
|50000003236|ESTADO DE KUWAIT (Estado independiente) - Persona Física|
|50000003244|LAOS - Persona Física|
|50000003252|LIBANO - Persona Física|
|50000003260|MALASIA - Persona Física|
|50000003279|REPUBLICA DE MALDIVAS (Estado independiente) - Persona Física|
|50000003287|SULTANATO DE OMAN - Persona Física|
|50000003295|MONGOLIA - Persona Física|
|50000003309|NEPAL - Persona Física|
|50000003317|EMIRATOS ARABES UNIDOS (Estado independiente) - Persona Física|
|50000003325|PAKISTAN - Persona Física|
|50000003333|SINGAPUR - Persona Física|
|50000003341|SIRIA - Persona Física|
|50000003376|VIETNAM - Persona Física|
|50000003392|REPUBLICA DEL YEMEN - Persona Física|
|50000003414|POS.BRITANICA (HONG KONG) - Persona Física|
|50000003422|POS.JAPONESA (ASIA) - Persona Física|
|50000003449|MACAO - Persona Física|
|50000003457|BANGLADESH - Persona Física|
|50000003503|TURQUIA - Persona Física|
|50000003546|ITALIA - Persona Física|
|50000003554|TURKMENISTAN - Persona Física|
|50000003562|UZBEKISTAN - Persona Física|
|50000003570|TERRITORIOS AUTONOMOS PALESTINOS - Persona Física|
|50000003813|ISLANDIA - Persona Física|
|50000003880|GEORGIA - Persona Física|
|50000003899|TAYIKISTAN - Persona Física|
|50000003902|AZERBAIDZHAN - Persona Física|
|50000003910|BRUNEI DARUSSALAM (Estado independiente) - Persona Física|
|50000003929|KAZAJSTAN - Persona Física|
|50000003937|KIRGUISTAN - Persona Física|
|50000003961|INDETERMINADO (ASIA) - Persona Física|
|50000004011|REPUBLICA DE ALBANIA - Persona Física|
|50000004046|PRINCIPADO DEL VALLE DE ANDORRA - Persona Física|
|50000004054|AUSTRIA - Persona Física|
|50000004062|BELGICA - Persona Física|
|50000004070|BULGARIA - Persona Física|
|50000004097|DINAMARCA - Persona Física|
|50000004100|ESPAÑA - Persona Física|
|50000004119|FINLANDIA - Persona Física|
|50000004127|FRANCIA - Persona Física|
|50000004135|GRECIA - Persona Física|
|50000004143|HUNGRIA - Persona Física|
|50000004151|IRLANDA (EIRE) - Persona Física|
|50000004186|PRINCIPADO DE LIECHTENSTEIN (Estado independiente) - Persona Física|
|50000004194|GRAN DUCADO DE LUXEMBURGO - Persona Física|
|50000004216|PRINCIPADO DE MONACO - Persona Física|
|50000004224|NORUEGA - Persona Física|
|50000004232|PAISES BAJOS - Persona Física|
|50000004240|POLONIA - Persona Física|
|50000004259|PORTUGAL - Persona Física|
|50000004267|REINO UNIDO - Persona Física|
|50000004275|RUMANIA - Persona Física|
|50000004283|SERENISIMA REPUBLICA DE SAN MARINO (Estado independiente) - Persona Física|
|50000004291|SUECIA - Persona Física|
|50000004305|SUIZA - Persona Física|
|50000004313|SANTA SEDE (VATICANO) - Persona Física|
|50000004321|YUGOSLAVIA - Persona Física|
|50000004364|REPUBLICA DE MALTA (Estado independiente) - Persona Física|
|50000004380|ALEMANIA, REP. FED. - Persona Física|
|50000004399|BIELORUSIA - Persona Física|
|50000004402|ESTONIA - Persona Física|
|50000004410|LETONIA - Persona Física|
|50000004429|LITUANIA - Persona Física|
|50000004437|MOLDOVA - Persona Física|
|50000004461|BOSNIA HERZEGOVINA - Persona Física|
|50000004496|ESLOVENIA - Persona Física|
|50000004909|MACEDONIA - Persona Física|
|50000004917|POS.BRITANICA (EUROPA) - Persona Física|
|50000004984|INDETERMINADO (EUROPA) - Persona Física|
|50000004992|AUSTRALIA - Persona Física|
|50000005034|REPUBLICA DE NAURU (Estado independiente) - Persona Física|
|50000005042|NUEVA ZELANDA - Persona Física|
|50000005050|REPUBLICA DE VANUATU - Persona Física|
|50000005069|SAMOA OCCIDENTAL - Persona Física|
|50000005077|POS.AUSTRALIANA (OCEANIA) - Persona Física|
|50000005085|POS.BRITANICA (OCEANIA) - Persona Física|
|50000005093|POS.FRANCESA (OCEANIA) - Persona Física|
|50000005107|POS.NEOCELANDESA (OCEANIA) - Persona Física|
|50000005115|POS.E.E.U.U. (OCEANIA) - Persona Física|
|50000005123|FIJI, ISLAS - Persona Física|
|50000005131|PAPUA, ISLAS - Persona Física|
|50000005166|KIRIBATI - Persona Física|
|50000005174|TUVALU - Persona Física|
|50000005182|ISLAS SALOMON - Persona Física|
|50000005190|REINO DE TONGA (Estado independiente) - Persona Física|
|50000005204|REPUBLICA DE LAS ISLAS MARSHALL (Estado independiente) - Persona Física|
|50000005212|ISLAS MARIANAS - Persona Física|
|50000005905|MICRONESIA ESTADOS FED. - Persona Física|
|50000005913|PALAU - Persona Física|
|50000005980|INDETERMINADO (OCEANIA) - Persona Física|
|50000006014|RUSA, FEDERACION - Persona Física|
|50000006022|ARMENIA - Persona Física|
|50000006030|CROACIA - Persona Física|
|50000006049|UCRANIA - Persona Física|
|50000006057|CHECA, REPUBLICA - Persona Física|
|50000006065|ESLOVACA, REPUBLICA - Persona Física|
|50000006529|ANGUILA (Territorio no autónomo del Reino Unido) - Persona Física|
|50000006537|ARUBA (Territorio de Países Bajos) - Persona Física|
|50000006545|ISLAS DE COOK (Territorio autónomo asociado a Nueva Zelanda) - Persona Física|
|50000006553|PATAU - Persona Física|
|50000006561|POLINESIA FRANCESA (Territorio de Ultramar de Francia) - Persona Física|
|50000006596|ANTILLAS HOLANDESAS (Territorio de Países Bajos) - Persona Física|
|50000006626|ASCENCION - Persona Física|
|50000006634|BERMUDAS (Territorio no autónomo del Reino Unido) - Persona Física|
|50000006642|CAMPIONE D@ITALIA - Persona Física|
|50000006650|COLONIA DE GIBRALTAR - Persona Física|
|50000006669|GROENLANDIA - Persona Física|
|50000006677|GUAM (Territorio no autónomo de los EEUU) - Persona Física|
|50000006685|HONK KONG (Territorio de China) - Persona Física|
|50000006693|ISLAS AZORES - Persona Física|
|50000006707|ISLAS DEL CANAL:Guernesey,Jersey,Alderney,G.Stark,L.Sark,etc - Persona Física|
|50000006715|ISLAS CAIMAN (Territorio no autónomo del Reino Unido) - Persona Física|
|50000006723|ISLA CHRISTMAS - Persona Física|
|50000006731|ISLA DE COCOS O KEELING - Persona Física|
|50000006766|ISLA DE MAN (Territorio del Reino Unido) - Persona Física|
|50000006774|ISLA DE NORFOLK - Persona Física|
|50000006782|ISLAS TURKAS Y CAICOS (Territorio no autónomo del R. Unido) - Persona Física|
|50000006790|ISLAS PACIFICO - Persona Física|
|50000006804|ISLA DE SAN PEDRO Y MIGUELON - Persona Física|
|50000006812|ISLA QESHM - Persona Física|
|50000006820|ISLAS VIRGENES BRITANICAS(Territorio no autónomo de R.UNIDO) - Persona Física|
|50000006839|ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA - Persona Física|
|50000006847|LABUAN - Persona Física|
|50000006855|MADEIRA (Territorio de Portugal) - Persona Física|
|50000006863|MONTSERRAT (Territorio no autónomo del Reino Unido) - Persona Física|
|50000006871|NIUE - Persona Física|
|50000006901|PITCAIRN - Persona Física|
|50000006936|REGIMEN APLICABLE A LAS SA FINANCIERAS(ley 11.073 de la ROU) - Persona Física|
|50000006944|SANTA ELENA - Persona Física|
|50000006952|SAMOA AMERICANA (Territorio no autónomo de los EEUU) - Persona Física|
|50000006960|ARCHIPIELAGO DE SVBALBARD - Persona Física|
|50000006979|TRISTAN DA CUNHA - Persona Física|
|50000006987|TRIESTE (Italia) - Persona Física|
|50000006995|TOKELAU - Persona Física|
|50000007002|ZONA LIBRE DE OSTRAVA (ciudad de la antigua Checoeslovaquia) - Persona Física|
|50000009986|PARA PERSONAS FISICAS DE INDETERMINADO (CONTINENTE) - Persona Física|
|50000009994|PARA PERSONAS FISICAS DE OTROS PAISES - Persona Física|
|51600000016|URUGUAY - Otro tipo de Entidad|
|51600000024|PARAGUAY - Otro tipo de Entidad|
|51600000032|CHILE - Otro tipo de Entidad|
|51600000040|BOLIVIA - Otro tipo de Entidad|
|51600000059|BRASIL - Otro tipo de Entidad|
|51600001012|BURKINA FASO - Otro tipo de Entidad|
|51600001020|ARGELIA - Otro tipo de Entidad|
|51600001039|BOTSWANA - Otro tipo de Entidad|
|51600001047|BURUNDI - Otro tipo de Entidad|
|51600001055|CAMERUN - Otro tipo de Entidad|
|51600001071|CENTRO AFRICANO, REP. - Otro tipo de Entidad|
|51600001101|COSTA DE MARFIL - Otro tipo de Entidad|
|51600001136|EGIPTO - Otro tipo de Entidad|
|51600001144|ETIOPIA - Otro tipo de Entidad|
|51600001152|GABON - Otro tipo de Entidad|
|51600001160|GAMBIA - Otro tipo de Entidad|
|51600001179|GHANA - Otro tipo de Entidad|
|51600001187|GUINEA - Otro tipo de Entidad|
|51600001195|GUINEA ECUATORIAL - Otro tipo de Entidad|
|51600001209|KENIA - Otro tipo de Entidad|
|51600001217|LESOTHO - Otro tipo de Entidad|
|51600001225|REPUBLICA DE LIBERIA (Estado independiente) - Otro tipo de Entidad|
|51600001233|LIBIA - Otro tipo de Entidad|
|51600001241|MADAGASCAR - Otro tipo de Entidad|
|51600001276|MARRUECOS - Otro tipo de Entidad|
|51600001284|REPUBLICA DE MAURICIO - Otro tipo de Entidad|
|51600001292|MAURITANIA - Otro tipo de Entidad|
|51600001306|NIGER - Otro tipo de Entidad|
|51600001314|NIGERIA - Otro tipo de Entidad|
|51600001322|ZIMBABWE - Otro tipo de Entidad|
|51600001330|RUANDA - Otro tipo de Entidad|
|51600001349|SENEGAL - Otro tipo de Entidad|
|51600001357|SIERRA LEONA - Otro tipo de Entidad|
|51600001365|SOMALIA - Otro tipo de Entidad|
|51600001373|REINO DE SWAZILANDIA (Estado independiente) - Otro tipo de Entidad|
|51600001381|SUDAN - Otro tipo de Entidad|
|51600001403|TOGO - Otro tipo de Entidad|
|51600001411|REPUBLICA TUNECINA - Otro tipo de Entidad|
|51600001446|ZAMBIA - Otro tipo de Entidad|
|51600001454|POS.BRITANICA (AFRICA) - Otro tipo de Entidad|
|51600001462|POS.ESPAÑOLA (AFRICA) - Otro tipo de Entidad|
|51600001470|POS.FRANCESA (AFRICA) - Otro tipo de Entidad|
|51600001489|POS.PORTUGUESA (AFRICA) - Otro tipo de Entidad|
|51600001497|REPUBLICA DE ANGOLA - Otro tipo de Entidad|
|51600001500|REPUBLICA DE CABO VERDE (Estado independiente) - Otro tipo de Entidad|
|51600001519|MOZAMBIQUE - Otro tipo de Entidad|
|51600001527|CONGO REP.POPULAR - Otro tipo de Entidad|
|51600001535|CHAD - Otro tipo de Entidad|
|51600001543|MALAWI - Otro tipo de Entidad|
|51600001551|TANZANIA - Otro tipo de Entidad|
|51600001586|COSTA RICA - Otro tipo de Entidad|
|51600001616|ZAIRE - Otro tipo de Entidad|
|51600001624|BENIN - Otro tipo de Entidad|
|51600001632|MALI - Otro tipo de Entidad|
|51600001705|UGANDA - Otro tipo de Entidad|
|51600001713|SUDAFRICA, REP. DE - Otro tipo de Entidad|
|51600001810|REPUBLICA DE SEYCHELLES (Estado independiente) - Otro tipo de Entidad|
|51600001829|SANTO TOME Y PRINCIPE - Otro tipo de Entidad|
|51600001837|NAMIBIA - Otro tipo de Entidad|
|51600001845|GUINEA BISSAU - Otro tipo de Entidad|
|51600001853|ERITREA - Otro tipo de Entidad|
|51600001861|REPUBLICA DE DJIBUTI (Estado independiente) - Otro tipo de Entidad|
|51600001896|COMORAS - Otro tipo de Entidad|
|51600001985|INDETERMINADO (AFRICA) - Otro tipo de Entidad|
|51600002019|BARBADOS (Estado independiente) - Otro tipo de Entidad|
|51600002043|CANADA - Otro tipo de Entidad|
|51600002051|COLOMBIA - Otro tipo de Entidad|
|51600002094|DOMINICANA, REPUBLICA - Otro tipo de Entidad|
|51600002116|EL SALVADOR - Otro tipo de Entidad|
|51600002124|ESTADOS UNIDOS - Otro tipo de Entidad|
|51600002132|GUATEMALA - Otro tipo de Entidad|
|51600002140|REPUBLICA COOPERATIVA DE GUYANA (Estado independiente) - Otro tipo de Entidad|
|51600002159|HAITI - Otro tipo de Entidad|
|51600002167|HONDURAS - Otro tipo de Entidad|
|51600002175|JAMAICA - Otro tipo de Entidad|
|51600002183|MEXICO - Otro tipo de Entidad|
|51600002191|NICARAGUA - Otro tipo de Entidad|
|51600002205|REPUBLICA DE PANAMA (Estado independiente) - Otro tipo de Entidad|
|51600002213|ESTADO LIBRE ASOCIADO DE PUERTO RICO (Estado asoc. a EEUU) - Otro tipo de Entidad|
|51600002221|PERU - Otro tipo de Entidad|
|51600002256|ANTIGUA Y BARBUDA (Estado independiente) - Otro tipo de Entidad|
|51600002264|VENEZUELA - Otro tipo de Entidad|
|51600002272|POS.BRITANICA (AMERICA) - Otro tipo de Entidad|
|51600002280|POS.DANESA (AMERICA) - Otro tipo de Entidad|
|51600002299|POS.FRANCESA (AMERICA) - Otro tipo de Entidad|
|51600002302|POS.PAISES BAJOS (AMERICA) - Otro tipo de Entidad|
|51600002310|POS.E.E.U.U. (AMERICA) - Otro tipo de Entidad|
|51600002329|SURINAME - Otro tipo de Entidad|
|51600002337|EL COMMONWEALTH DE DOMINICA (Estado Asociado) - Otro tipo de Entidad|
|51600002345|SANTA LUCIA - Otro tipo de Entidad|
|51600002353|SAN VICENTE Y LAS GRANADINAS (Estado independiente) - Otro tipo de Entidad|
|51600002361|BELICE (Estado independiente) - Otro tipo de Entidad|
|51600002396|CUBA - Otro tipo de Entidad|
|51600002426|ECUADOR - Otro tipo de Entidad|
|51600002434|REPUBLICA DE TRINIDAD Y TOBAGO - Otro tipo de Entidad|
|51600002825|BUTAN - Otro tipo de Entidad|
|51600002841|MYANMAR (EX BIRMANIA) - Otro tipo de Entidad|
|51600002876|ISRAEL - Otro tipo de Entidad|
|51600002884|ESTADO ASOCIADO DE GRANADA (Estado independiente) - Otro tipo de Entidad|
|51600002892|FEDERACION DE SAN CRISTOBAL (Islas Saint Kitts and Nevis) - Otro tipo de Entidad|
|51600002906|COMUNIDAD DE LAS BAHAMAS (Estado independiente) - Otro tipo de Entidad|
|51600002914|TAILANDIA - Otro tipo de Entidad|
|51600002922|INDETERMINADO (AMERICA) - Otro tipo de Entidad|
|51600002930|IRAN - Otro tipo de Entidad|
|51600002981|ESTADO DE QATAR (Estado independiente) - Otro tipo de Entidad|
|51600003007|REINO HACHEMITA DE JORDANIA - Otro tipo de Entidad|
|51600003015|AFGANISTAN - Otro tipo de Entidad|
|51600003023|ARABIA SAUDITA - Otro tipo de Entidad|
|51600003031|ESTADO DE BAHREIN (Estado independiente) - Otro tipo de Entidad|
|51600003066|CAMBOYA (EX KAMPUCHEA) - Otro tipo de Entidad|
|51600003074|REPUBLICA DEMOCRATICA SOCIALISTA DE SRI LANKA - Otro tipo de Entidad|
|51600003082|COREA DEMOCRATICA  - Otro tipo de Entidad|
|51600003090|COREA REPUBLICANA - Otro tipo de Entidad|
|51600003104|CHINA REP.POPULAR - Otro tipo de Entidad|
|51600003112|REPUBLICA DE CHIPRE (Estado independiente) - Otro tipo de Entidad|
|51600003120|FILIPINAS - Otro tipo de Entidad|
|51600003139|TAIWAN - Otro tipo de Entidad|
|51600003147|GAZA - Otro tipo de Entidad|
|51600003155|INDIA - Otro tipo de Entidad|
|51600003163|INDONESIA - Otro tipo de Entidad|
|51600003171|IRAK - Otro tipo de Entidad|
|51600003201|JAPON - Otro tipo de Entidad|
|51600003236|ESTADO DE KUWAIT (Estado independiente) - Otro tipo de Entidad|
|51600003244|LAOS - Otro tipo de Entidad|
|51600003252|LIBANO - Otro tipo de Entidad|
|51600003260|MALASIA - Otro tipo de Entidad|
|51600003279|REPUBLICA DE MALDIVAS (Estado independiente) - Otro tipo de Entidad|
|51600003287|SULTANATO DE OMAN - Otro tipo de Entidad|
|51600003295|MONGOLIA - Otro tipo de Entidad|
|51600003309|NEPAL - Otro tipo de Entidad|
|51600003317|EMIRATOS ARABES UNIDOS (Estado independiente) - Otro tipo de Entidad|
|51600003325|PAKISTAN - Otro tipo de Entidad|
|51600003333|SINGAPUR - Otro tipo de Entidad|
|51600003341|SIRIA - Otro tipo de Entidad|
|51600003376|VIETNAM - Otro tipo de Entidad|
|51600003392|REPUBLICA DEL YEMEN - Otro tipo de Entidad|
|51600003414|POS.BRITANICA (HONG KONG) - Otro tipo de Entidad|
|51600003422|POS.JAPONESA (ASIA) - Otro tipo de Entidad|
|51600003449|MACAO - Otro tipo de Entidad|
|51600003457|BANGLADESH - Otro tipo de Entidad|
|51600003503|TURQUIA - Otro tipo de Entidad|
|51600003546|ITALIA - Otro tipo de Entidad|
|51600003554|TURKMENISTAN - Otro tipo de Entidad|
|51600003562|UZBEKISTAN - Otro tipo de Entidad|
|51600003570|TERRITORIOS AUTONOMOS PALESTINOS - Otro tipo de Entidad|
|51600003813|ISLANDIA - Otro tipo de Entidad|
|51600003880|GEORGIA - Otro tipo de Entidad|
|51600003899|TAYIKISTAN - Otro tipo de Entidad|
|51600003902|AZERBAIDZHAN - Otro tipo de Entidad|
|51600003910|BRUNEI DARUSSALAM (Estado independiente) - Otro tipo de Entidad|
|51600003929|KAZAJSTAN - Otro tipo de Entidad|
|51600003937|KIRGUISTAN - Otro tipo de Entidad|
|51600003961|INDETERMINADO (ASIA) - Otro tipo de Entidad|
|51600004011|REPUBLICA DE ALBANIA - Otro tipo de Entidad|
|51600004046|PRINCIPADO DEL VALLE DE ANDORRA - Otro tipo de Entidad|
|51600004054|AUSTRIA - Otro tipo de Entidad|
|51600004062|BELGICA - Otro tipo de Entidad|
|51600004070|BULGARIA - Otro tipo de Entidad|
|51600004097|DINAMARCA - Otro tipo de Entidad|
|51600004100|ESPAÑA - Otro tipo de Entidad|
|51600004119|FINLANDIA - Otro tipo de Entidad|
|51600004127|FRANCIA - Otro tipo de Entidad|
|51600004135|GRECIA - Otro tipo de Entidad|
|51600004143|HUNGRIA - Otro tipo de Entidad|
|51600004151|IRLANDA (EIRE) - Otro tipo de Entidad|
|51600004186|PRINCIPADO DE LIECHTENSTEIN (Estado independiente) - Otro tipo de Entidad|
|51600004194|GRAN DUCADO DE LUXEMBURGO - Otro tipo de Entidad|
|51600004216|PRINCIPADO DE MONACO - Otro tipo de Entidad|
|51600004224|NORUEGA - Otro tipo de Entidad|
|51600004232|PAISES BAJOS - Otro tipo de Entidad|
|51600004240|POLONIA - Otro tipo de Entidad|
|51600004259|PORTUGAL - Otro tipo de Entidad|
|51600004267|REINO UNIDO - Otro tipo de Entidad|
|51600004275|RUMANIA - Otro tipo de Entidad|
|51600004283|SERENISIMA REPUBLICA DE SAN MARINO (Estado independiente) - Otro tipo de Entidad|
|51600004291|SUECIA - Otro tipo de Entidad|
|51600004305|SUIZA - Otro tipo de Entidad|
|51600004313|SANTA SEDE (VATICANO) - Otro tipo de Entidad|
|51600004321|YUGOSLAVIA - Otro tipo de Entidad|
|51600004364|REPUBLICA DE MALTA (Estado independiente) - Otro tipo de Entidad|
|51600004380|ALEMANIA, REP. FED. - Otro tipo de Entidad|
|51600004399|BIELORUSIA - Otro tipo de Entidad|
|51600004402|ESTONIA - Otro tipo de Entidad|
|51600004410|LETONIA - Otro tipo de Entidad|
|51600004429|LITUANIA - Otro tipo de Entidad|
|51600004437|MOLDOVA - Otro tipo de Entidad|
|51600004461|BOSNIA HERZEGOVINA - Otro tipo de Entidad|
|51600004496|ESLOVENIA - Otro tipo de Entidad|
|51600004909|MACEDONIA - Otro tipo de Entidad|
|51600004917|POS.BRITANICA (EUROPA) - Otro tipo de Entidad|
|51600004984|INDETERMINADO (EUROPA) - Otro tipo de Entidad|
|51600004992|AUSTRALIA - Otro tipo de Entidad|
|51600005034|REPUBLICA DE NAURU (Estado independiente) - Otro tipo de Entidad|
|51600005042|NUEVA ZELANDA - Otro tipo de Entidad|
|51600005050|REPUBLICA DE VANUATU - Otro tipo de Entidad|
|51600005069|SAMOA OCCIDENTAL - Otro tipo de Entidad|
|51600005077|POS.AUSTRALIANA (OCEANIA) - Otro tipo de Entidad|
|51600005085|POS.BRITANICA (OCEANIA) - Otro tipo de Entidad|
|51600005093|POS.FRANCESA (OCEANIA) - Otro tipo de Entidad|
|51600005107|POS.NEOCELANDESA (OCEANIA) - Otro tipo de Entidad|
|51600005115|POS.E.E.U.U. (OCEANIA) - Otro tipo de Entidad|
|51600005123|FIJI, ISLAS - Otro tipo de Entidad|
|51600005131|PAPUA, ISLAS - Otro tipo de Entidad|
|51600005166|KIRIBATI - Otro tipo de Entidad|
|51600005174|TUVALU - Otro tipo de Entidad|
|51600005182|ISLAS SALOMON - Otro tipo de Entidad|
|51600005190|REINO DE TONGA (Estado independiente) - Otro tipo de Entidad|
|51600005204|REPUBLICA DE LAS ISLAS MARSHALL (Estado independiente) - Otro tipo de Entidad|
|51600005212|ISLAS MARIANAS - Otro tipo de Entidad|
|51600005905|MICRONESIA ESTADOS FEDERADOS - Otro tipo de Entidad|
|51600005913|PALAU - Otro tipo de Entidad|
|51600005980|INDETERMINADO (OCEANIA) - Otro tipo de Entidad|
|51600006014|RUSA, FEDERACION - Otro tipo de Entidad|
|51600006022|ARMENIA - Otro tipo de Entidad|
|51600006030|CROACIA - Otro tipo de Entidad|
|51600006049|UCRANIA - Otro tipo de Entidad|
|51600006057|CHECA, REPUBLICA - Otro tipo de Entidad|
|51600006065|ESLOVACA, REPUBLICA - Otro tipo de Entidad|
|51600006529|ANGUILA (Territorio no autónomo del Reino Unido) - Otro tipo de Entidad|
|51600006537|ARUBA (Territorio de Países Bajos) - Otro tipo de Entidad|
|51600006545|ISLAS DE COOK (Territorio autónomo asociado a Nueva Zelanda) - Otro tipo de Entidad|
|51600006553|PATAU - Otro tipo de Entidad|
|51600006561|POLINESIA FRANCESA (Territorio de Ultramar de Francia) - Otro tipo de Entidad|
|51600006596|ANTILLAS HOLANDESAS (Territorio de Países Bajos) - Otro tipo de Entidad|
|51600006626|ASCENCION - Otro tipo de Entidad|
|51600006634|BERMUDAS (Territorio no autónomo del Reino Unido) - Otro tipo de Entidad|
|51600006642|CAMPIONE D@ITALIA - Otro tipo de Entidad|
|51600006650|COLONIA DE GIBRALTAR - Otro tipo de Entidad|
|51600006669|GROENLANDIA - Otro tipo de Entidad|
|51600006677|GUAM (Territorio no autónomo de los EEUU) - Otro tipo de Entidad|
|51600006685|HONK KONG (Territorio de China) - Otro tipo de Entidad|
|51600006693|ISLAS AZORES - Otro tipo de Entidad|
|51600006707|ISLAS DEL CANAL:Guernesey,Jersey,Alderney,G.Stark,L.Sark,etc - Otro tipo de Entidad|
|51600006715|ISLAS CAIMAN (Territorio no autónomo del Reino Unido) - Otro tipo de Entidad|
|51600006723|ISLA CHRISTMAS - Otro tipo de Entidad|
|51600006731|ISLA DE COCOS O KEELING - Otro tipo de Entidad|
|51600006766|ISLA DE MAN (Territorio del Reino Unido) - Otro tipo de Entidad|
|51600006774|ISLA DE NORFOLK - Otro tipo de Entidad|
|51600006782|ISLAS TURKAS Y CAICOS (Territorio no autónomo del R. Unido) - Otro tipo de Entidad|
|51600006790|ISLAS PACIFICO - Otro tipo de Entidad|
|51600006804|ISLA DE SAN PEDRO Y MIGUELON - Otro tipo de Entidad|
|51600006812|ISLA QESHM - Otro tipo de Entidad|
|51600006820|ISLAS VIRGENES BRITANICAS(Territorio no autónomo de R.UNIDO) - Otro tipo de Entidad|
|51600006839|ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA - Otro tipo de Entidad|
|51600006847|LABUAN - Otro tipo de Entidad|
|51600006855|MADEIRA (Territorio de Portugal) - Otro tipo de Entidad|
|51600006863|MONTSERRAT (Territorio no autónomo del Reino Unido) - Otro tipo de Entidad|
|51600006871|NIUE - Otro tipo de Entidad|
|51600006901|PITCAIRN - Otro tipo de Entidad|
|51600006936|REGIMEN APLICABLE A LAS SA FINANCIERAS(ley 11.073 de la ROU) - Otro tipo de Entidad|
|51600006944|SANTA ELENA - Otro tipo de Entidad|
|51600006952|SAMOA AMERICANA (Territorio no autónomo de los EEUU) - Otro tipo de Entidad|
|51600006960|ARCHIPIELAGO DE SVBALBARD - Otro tipo de Entidad|
|51600006979|TRISTAN DA CUNHA - Otro tipo de Entidad|
|51600006987|TRIESTE (Italia) - Otro tipo de Entidad|
|51600006995|TOKELAU - Otro tipo de Entidad|
|51600007002|ZONA LIBRE DE OSTRAVA (ciudad de la antigua Checoeslovaquia) - Otro tipo de Entidad|
|51600009986|PARA PERSONAS FISICAS DE INDETERMINADO (CONTINENTE) - Otro tipo de Entidad|
|51600009994|PARA PERSONAS FISICAS DE OTROS PAISES - Otro tipo de Entidad|
|55000000018|URUGUAY - Persona Jurídica|
|55000000026|PARAGUAY - Persona Jurídica|
|55000000034|CHILE - Persona Jurídica|
|55000000042|BOLIVIA - Persona Jurídica|
|55000000050|BRASIL - Persona Jurídica|
|55000001014|BURKINA FASO - Persona Jurídica|
|55000001022|ARGELIA - Persona Jurídica|
|55000001030|BOTSWANA - Persona Jurídica|
|55000001049|BURUNDI - Persona Jurídica|
|55000001057|CAMERUN - Persona Jurídica|
|55000001073|CENTRO AFRICANO, REP. - Persona Jurídica|
|55000001103|COSTA DE MARFIL - Persona Jurídica|
|55000001138|EGIPTO - Persona Jurídica|
|55000001146|ETIOPIA - Persona Jurídica|
|55000001154|GABON - Persona Jurídica|
|55000001162|GAMBIA - Persona Jurídica|
|55000001170|GHANA - Persona Jurídica|
|55000001189|GUINEA - Persona Jurídica|
|55000001197|GUINEA ECUATORIAL - Persona Jurídica|
|55000001200|KENIA - Persona Jurídica|
|55000001219|LESOTHO - Persona Jurídica|
|55000001227|REPUBLICA DE LIBERIA (Estado independiente) - Persona Jurídica|
|55000001235|LIBIA - Persona Jurídica|
|55000001243|MADAGASCAR - Persona Jurídica|
|55000001278|MARRUECOS - Persona Jurídica|
|55000001286|REPUBLICA DE MAURICIO - Persona Jurídica|
|55000001294|MAURITANIA - Persona Jurídica|
|55000001308|NIGER - Persona Jurídica|
|55000001316|NIGERIA - Persona Jurídica|
|55000001324|ZIMBABWE - Persona Jurídica|
|55000001332|RUANDA - Persona Jurídica|
|55000001340|SENEGAL - Persona Jurídica|
|55000001359|SIERRA LEONA - Persona Jurídica|
|55000001367|SOMALIA - Persona Jurídica|
|55000001375|REINO DE SWAZILANDIA (Estado independiente) - Persona Jurídica|
|55000001383|SUDAN - Persona Jurídica|
|55000001405|TOGO - Persona Jurídica|
|55000001413|REPUBLICA TUNECINA - Persona Jurídica|
|55000001448|ZAMBIA - Persona Jurídica|
|55000001456|POS.BRITANICA (AFRICA) - Persona Jurídica|
|55000001464|POS.ESPAÑOLA (AFRICA) - Persona Jurídica|
|55000001472|POS.FRANCESA (AFRICA) - Persona Jurídica|
|55000001480|POS.PORTUGUESA (AFRICA) - Persona Jurídica|
|55000001499|REPUBLICA DE ANGOLA - Persona Jurídica|
|55000001502|REPUBLICA DE CABO VERDE (Estado independiente) - Persona Jurídica|
|55000001510|MOZAMBIQUE - Persona Jurídica|
|55000001529|CONGO REP.POPULAR - Persona Jurídica|
|55000001537|CHAD - Persona Jurídica|
|55000001545|MALAWI - Persona Jurídica|
|55000001553|TANZANIA - Persona Jurídica|
|55000001588|COSTA RICA - Persona Jurídica|
|55000001618|ZAIRE - Persona Jurídica|
|55000001626|BENIN - Persona Jurídica|
|55000001634|MALI - Persona Jurídica|
|55000001707|UGANDA - Persona Jurídica|
|55000001715|SUDAFRICA, REP. DE - Persona Jurídica|
|55000001812|REPUBLICA DE SEYCHELLES (Estado independiente) - Persona Jurídica|
|55000001820|SANTO TOME Y PRINCIPE - Persona Jurídica|
|55000001839|NAMIBIA - Persona Jurídica|
|55000001847|GUINEA BISSAU - Persona Jurídica|
|55000001855|ERITREA - Persona Jurídica|
|55000001863|REPUBLICA DE DJIBUTI (Estado independiente) - Persona Jurídica|
|55000001898|COMORAS - Persona Jurídica|
|55000001987|INDETERMINADO (AFRICA) - Persona Jurídica|
|55000002010|BARBADOS (Estado independiente) - Persona Jurídica|
|55000002045|CANADA - Persona Jurídica|
|55000002053|COLOMBIA - Persona Jurídica|
|55000002096|DOMINICANA, REPUBLICA - Persona Jurídica|
|55000002118|EL SALVADOR - Persona Jurídica|
|55000002126|ESTADOS UNIDOS - Persona Jurídica|
|55000002134|GUATEMALA - Persona Jurídica|
|55000002142|REPUBLICA COOPERATIVA DE GUYANA (Estado independiente) - Persona Jurídica|
|55000002150|HAITI - Persona Jurídica|
|55000002169|HONDURAS - Persona Jurídica|
|55000002177|JAMAICA - Persona Jurídica|
|55000002185|MEXICO - Persona Jurídica|
|55000002193|NICARAGUA - Persona Jurídica|
|55000002207|REPUBLICA DE PANAMA (Estado independiente) - Persona Jurídica|
|55000002215|ESTADO LIBRE ASOCIADO DE PUERTO RICO (Estado asoc. a EEUU) - Persona Jurídica|
|55000002223|PERU - Persona Jurídica|
|55000002258|ANTIGUA Y BARBUDA (Estado independiente) - Persona Jurídica|
|55000002266|VENEZUELA - Persona Jurídica|
|55000002274|POS.BRITANICA (AMERICA) - Persona Jurídica|
|55000002282|POS.DANESA (AMERICA) - Persona Jurídica|
|55000002290|POS.FRANCESA (AMERICA) - Persona Jurídica|
|55000002304|POS.PAISES BAJOS (AMERICA) - Persona Jurídica|
|55000002312|POS.E.E.U.U. (AMERICA) - Persona Jurídica|
|55000002320|SURINAME - Persona Jurídica|
|55000002339|EL COMMONWEALTH DE DOMINICA (Estado Asociado) - Persona Jurídica|
|55000002347|SANTA LUCIA - Persona Jurídica|
|55000002355|SAN VICENTE Y LAS GRANADINAS (Estado independiente) - Persona Jurídica|
|55000002363|BELICE (Estado independiente) - Persona Jurídica|
|55000002398|CUBA - Persona Jurídica|
|55000002428|ECUADOR - Persona Jurídica|
|55000002436|REPUBLICA DE TRINIDAD Y TOBAGO - Persona Jurídica|
|55000002827|BUTAN - Persona Jurídica|
|55000002843|MYANMAR (EX BIRMANIA) - Persona Jurídica|
|55000002878|ISRAEL - Persona Jurídica|
|55000002884|ESTADO ASOCIADO DE GRANADA (Estado independiente) - Persona Jurídica|
|55000002894|FEDERACION DE SAN CRISTOBAL (Islas Saint Kitts and Nevis) - Persona Jurídica|
|55000002908|COMUNIDAD DE LAS BAHAMAS (Estado independiente) - Persona Jurídica|
|55000002916|TAILANDIA - Persona Jurídica|
|55000002924|INDETERMINADO (AMERICA) - Persona Jurídica|
|55000002932|IRAN - Persona Jurídica|
|55000002983|ESTADO DE QATAR (Estado independiente) - Persona Jurídica|
|55000003009|REINO HACHEMITA DE JORDANIA - Persona Jurídica|
|55000003017|AFGANISTAN - Persona Jurídica|
|55000003025|ARABIA SAUDITA - Persona Jurídica|
|55000003033|ESTADO DE BAHREIN (Estado independiente) - Persona Jurídica|
|55000003068|CAMBOYA (EX KAMPUCHEA) - Persona Jurídica|
|55000003076|REPUBLICA DEMOCRATICA SOCIALISTA DE SRI LANKA - Persona Jurídica|
|55000003084|COREA DEMOCRATICA  - Persona Jurídica|
|55000003092|COREA REPUBLICANA - Persona Jurídica|
|55000003106|CHINA REP.POPULAR - Persona Jurídica|
|55000003114|REPUBLICA DE CHIPRE (Estado independiente) - Persona Jurídica|
|55000003122|FILIPINAS - Persona Jurídica|
|55000003130|TAIWAN - Persona Jurídica|
|55000003149|GAZA - Persona Jurídica|
|55000003157|INDIA - Persona Jurídica|
|55000003165|INDONESIA - Persona Jurídica|
|55000003173|IRAK - Persona Jurídica|
|55000003203|JAPON - Persona Jurídica|
|55000003238|ESTADO DE KUWAIT (Estado independiente) - Persona Jurídica|
|55000003246|LAOS - Persona Jurídica|
|55000003254|LIBANO - Persona Jurídica|
|55000003262|MALASIA - Persona Jurídica|
|55000003270|REPUBLICA DE MALDIVAS (Estado independiente) - Persona Jurídica|
|55000003289|SULTANATO DE OMAN - Persona Jurídica|
|55000003297|MONGOLIA - Persona Jurídica|
|55000003300|NEPAL - Persona Jurídica|
|55000003319|EMIRATOS ARABES UNIDOS (Estado independiente) - Persona Jurídica|
|55000003327|PAKISTAN - Persona Jurídica|
|55000003335|SINGAPUR - Persona Jurídica|
|55000003343|SIRIA - Persona Jurídica|
|55000003378|VIETNAM - Persona Jurídica|
|55000003394|REPUBLICA DEL YEMEN - Persona Jurídica|
|55000003416|POS.BRITANICA (HONG KONG) - Persona Jurídica|
|55000003424|POS.JAPONESA (ASIA) - Persona Jurídica|
|55000003440|MACAO - Persona Jurídica|
|55000003459|BANGLADESH - Persona Jurídica|
|55000003505|TURQUIA - Persona Jurídica|
|55000003548|ITALIA - Persona Jurídica|
|55000003556|TURKMENISTAN - Persona Jurídica|
|55000003564|UZBEKISTAN - Persona Jurídica|
|55000003572|TERRITORIOS AUTONOMOS PALESTINOS - Persona Jurídica|
|55000003815|ISLANDIA - Persona Jurídica|
|55000003882|GEORGIA - Persona Jurídica|
|55000003890|TAYIKISTAN - Persona Jurídica|
|55000003904|AZERBAIDZHAN - Persona Jurídica|
|55000003912|BRUNEI DARUSSALAM (Estado independiente) - Persona Jurídica|
|55000003920|KAZAJSTAN - Persona Jurídica|
|55000003939|KIRGUISTAN - Persona Jurídica|
|55000003963|INDETERMINADO (ASIA) - Persona Jurídica|
|55000004013|REPUBLICA DE ALBANIA - Persona Jurídica|
|55000004048|PRINCIPADO DEL VALLE DE ANDORRA - Persona Jurídica|
|55000004056|AUSTRIA - Persona Jurídica|
|55000004064|BELGICA - Persona Jurídica|
|55000004072|BULGARIA - Persona Jurídica|
|55000004099|DINAMARCA - Persona Jurídica|
|55000004102|ESPAÑA - Persona Jurídica|
|55000004110|FINLANDIA - Persona Jurídica|
|55000004129|FRANCIA - Persona Jurídica|
|55000004137|GRECIA - Persona Jurídica|
|55000004145|HUNGRIA - Persona Jurídica|
|55000004153|IRLANDA (EIRE) - Persona Jurídica|
|55000004188|PRINCIPADO DE LIECHTENSTEIN (Estado independiente) - Persona Jurídica|
|55000004196|GRAN DUCADO DE LUXEMBURGO - Persona Jurídica|
|55000004218|PRINCIPADO DE MONACO - Persona Jurídica|
|55000004226|NORUEGA - Persona Jurídica|
|55000004234|PAISES BAJOS - Persona Jurídica|
|55000004242|POLONIA - Persona Jurídica|
|55000004250|PORTUGAL - Persona Jurídica|
|55000004269|REINO UNIDO - Persona Jurídica|
|55000004277|RUMANIA - Persona Jurídica|
|55000004285|SERENISIMA REPUBLICA DE SAN MARINO (Estado independiente) - Persona Jurídica|
|55000004293|SUECIA - Persona Jurídica|
|55000004307|SUIZA - Persona Jurídica|
|55000004315|SANTA SEDE (VATICANO) - Persona Jurídica|
|55000004323|YUGOSLAVIA - Persona Jurídica|
|55000004366|REPUBLICA DE MALTA (Estado independiente) - Persona Jurídica|
|55000004382|ALEMANIA, REP. FED. - Persona Jurídica|
|55000004390|BIELORUSIA - Persona Jurídica|
|55000004404|ESTONIA - Persona Jurídica|
|55000004412|LETONIA - Persona Jurídica|
|55000004420|LITUANIA - Persona Jurídica|
|55000004439|MOLDOVA - Persona Jurídica|
|55000004463|BOSNIA HERZEGOVINA - Persona Jurídica|
|55000004498|ESLOVENIA - Persona Jurídica|
|55000004900|MACEDONIA - Persona Jurídica|
|55000004919|POS.BRITANICA (EUROPA) - Persona Jurídica|
|55000004986|INDETERMINADO (EUROPA) - Persona Jurídica|
|55000004994|AUSTRALIA - Persona Jurídica|
|55000005036|REPUBLICA DE NAURU (Estado independiente) - Persona Jurídica|
|55000005044|NUEVA ZELANDA - Persona Jurídica|
|55000005052|REPUBLICA DE VANUATU - Persona Jurídica|
|55000005069|SAMOA OCCIDENTAL - Persona Jurídica|
|55000005079|POS.AUSTRALIANA (OCEANIA) - Persona Jurídica|
|55000005087|POS.BRITANICA (OCEANIA) - Persona Jurídica|
|55000005095|POS.FRANCESA (OCEANIA) - Persona Jurídica|
|55000005109|POS.NEOCELANDESA (OCEANIA) - Persona Jurídica|
|55000005117|POS.E.E.U.U. (OCEANIA) - Persona Jurídica|
|55000005125|FIJI, ISLAS - Persona Jurídica|
|55000005133|PAPUA, ISLAS - Persona Jurídica|
|55000005168|KIRIBATI - Persona Jurídica|
|55000005176|TUVALU - Persona Jurídica|
|55000005184|ISLAS SALOMON - Persona Jurídica|
|55000005192|REINO DE TONGA (Estado independiente) - Persona Jurídica|
|55000005206|REPUBLICA DE LAS ISLAS MARSHALL (Estado independiente) - Persona Jurídica|
|55000005214|ISLAS MARIANAS - Persona Jurídica|
|55000005907|MICRONESIA ESTADOS FED. - Persona Jurídica|
|55000005915|PALAU - Persona Jurídica|
|55000005982|INDETERMINADO (OCEANIA) - Persona Jurídica|
|55000006016|RUSA, FEDERACION - Persona Jurídica|
|55000006024|ARMENIA - Persona Jurídica|
|55000006032|CROACIA - Persona Jurídica|
|55000006040|UCRANIA - Persona Jurídica|
|55000006059|CHECA, REPUBLICA - Persona Jurídica|
|55000006067|ESLOVACA, REPUBLICA - Persona Jurídica|
|55000006520|ANGUILA (Territorio no autónomo del Reino Unido) - Persona Jurídica|
|55000006539|ARUBA (Territorio de Países Bajos) - Persona Jurídica|
|55000006547|ISLAS DE COOK (Territorio autónomo asociado a Nueva Zelanda) - Persona Jurídica|
|55000006555|PATAU - Persona Jurídica|
|55000006563|POLINESIA FRANCESA (Territorio de Ultramar de Francia) - Persona Jurídica|
|55000006598|ANTILLAS HOLANDESAS (Territorio de Países Bajos) - Persona Jurídica|
|55000006628|ASCENCION - Persona Jurídica|
|55000006636|BERMUDAS (Territorio no autónomo del Reino Unido) - Persona Jurídica|
|55000006644|CAMPIONE D@ITALIA - Persona Jurídica|
|55000006652|COLONIA DE GIBRALTAR - Persona Jurídica|
|55000006660|GROENLANDIA - Persona Jurídica|
|55000006679|GUAM (Territorio no autónomo de los EEUU) - Persona Jurídica|
|55000006687|HONK KONG (Territorio de China) - Persona Jurídica|
|55000006695|ISLAS AZORES - Persona Jurídica|
|55000006709|ISLAS DEL CANAL:Guernesey,Jersey,Alderney,G.Stark,L.Sark,etc - Persona Jurídica|
|55000006717|ISLAS CAIMAN (Territorio no autónomo del Reino Unido) - Persona Jurídica|
|55000006725|ISLA CHRISTMAS - Persona Jurídica|
|55000006733|ISLA DE COCOS O KEELING - Persona Jurídica|
|55000006768|ISLA DE MAN (Territorio del Reino Unido) - Persona Jurídica|
|55000006776|ISLA DE NORFOLK - Persona Jurídica|
|55000006784|ISLAS TURKAS Y CAICOS (Territorio no autónomo del R. Unido) - Persona Jurídica|
|55000006792|ISLAS PACIFICO - Persona Jurídica|
|55000006806|ISLA DE SAN PEDRO Y MIGUELON - Persona Jurídica|
|55000006814|ISLA QESHM - Persona Jurídica|
|55000006822|ISLAS VIRGENES BRITANICAS(Territorio no autónomo de R.UNIDO) - Persona Jurídica|
|55000006830|ISLAS VIRGENES DE ESTADOS UNIDOS DE AMERICA - Persona Jurídica|
|55000006849|LABUAN - Persona Jurídica|
|55000006857|MADEIRA (Territorio de Portugal) - Persona Jurídica|
|55000006865|MONTSERRAT (Territorio no autónomo del Reino Unido) - Persona Jurídica|
|55000006873|NIUE - Persona Jurídica|
|55000006903|PITCAIRN - Persona Jurídica|
|55000006938|REGIMEN APLICABLE A LAS SA FINANCIERAS(ley 11.073 de la ROU) - Persona Jurídica|
|55000006946|SANTA ELENA - Persona Jurídica|
|55000006954|SAMOA AMERICANA (Territorio no autónomo de los EEUU) - Persona Jurídica|
|55000006962|ARCHIPIELAGO DE SVBALBARD - Persona Jurídica|
|55000006970|TRISTAN DA CUNHA - Persona Jurídica|
|55000006989|TRIESTE (Italia) - Persona Jurídica|
|55000006997|TOKELAU - Persona Jurídica|
|55000007004|ZONA LIBRE DE OSTRAVA (ciudad de la antigua Checoeslovaquia) - Persona Jurídica|
|55000009988|PARA PERSONAS FISICAS DE INDETERMINADO (CONTINENTE) - Persona Jurídica|
|55000009996|PARA PERSONAS FISICAS DE OTROS PAISES - Persona Jurídica|