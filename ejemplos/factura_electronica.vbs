' 
' Ejemplo de Uso de Interfaz PyAfipWs para Windows Script Host
' con Web Service Autenticaci�n / Factura Electr�nica AFIP
' 20134(C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
'  Requerimientos: scripts wsaa.py y wsfev1.py registrados
' Documentacion: 
'  http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
'  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 
' Crear el objeto WSAA (Web Service de Autenticaci�n y Autorizaci�n) AFIP
Set WSAA = Wscript.CreateObject("WSAA")
Wscript.Echo "InstallDir", WSAA.InstallDir, WSAA.Version

' Solicitar Ticket de Acceso
wsdl = "https://wsaa.afip.gov.ar/ws/services/LoginCms" ' Producci�n!
scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ok = WSAA.Autenticar("wsfe", scriptdir & "\..\reingart.crt", scriptdir & "\..\reingart.key", wsdl)
Wscript.Echo "Excepcion", WSAA.Excepcion
Wscript.Echo "Token", WSAA.Token
Wscript.Echo "Sign", WSAA.Sign

' Crear el objeto WSFEv1 (Web Service de Factura Electr�nica version 1) AFIP

Set WSFEv1 = Wscript.CreateObject("WSFEv1")
Wscript.Echo "InstallDir", WSFEv1.InstallDir, WSFEv1.Version

' Establecer parametros de uso:
WSFEv1.Cuit = "20267565393"
WSFEv1.Token = WSAA.Token
WSFEv1.Sign = WSAA.Sign

' Conectar al websrvice
WSFEv1.Conectar

' Consultar �ltimo comprobante autorizado en AFIP
tipo_cbte = 1
pto_vta = 1
ult = WSFEv1.CompUltimoAutorizado(tipo_cbte, pto_vta)
Wscript.Echo "Ultimo comprobante: ", ult 
Wscript.Echo WSFEv1.Excepcion, "Excepcion"
