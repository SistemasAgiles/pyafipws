#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""M�dulo para obtener c�digo de autorizaci�n electr�nico del web service 
WSMTX de AFIP (Factura Electr�nica Mercado Interno RG2904 opci�n A con detalle)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.09c"

import datetime
import decimal
import os
import socket
import sys
import traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper
from cStringIO import StringIO
from utils import verifica

HOMO = False

WSDL="https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"

def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CAE = self.Vencimiento = ""
            self.Evento = self.Obs = ""
            self.FechaCbte = self.CbteNro = self.PuntoVenta = self.ImpTotal = None
            self.Errores = []
            self.Observaciones = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = ""
            self.ErrMsg = ""
            self.CAEA = ""
            self.Periodo = self.Orden = ""
            self.FchVigDesde = self.FchVigHasta = ""
            self.FchTopeInf = self.FchProceso = ""

            # llamo a la funci�n (con reintentos)
            retry = 5
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] != 10054:
                        # solo reintentar si el error es de conexi�n
                        # (10054, 'Connection reset by peer')
                        raise
        
        except SoapFault, e:
            # guardo destalle de la excepci�n SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = u"%s" % (e)
            raise
        finally:
            # guardo datos de depuraci�n
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper
    
class WSMTXCA:
    "Interfaz para el WebService de Factura Electr�nica Mercado Interno WSMTXCA"
    _public_methods_ = ['CrearFactura', 'EstablecerCampoFactura', 'AgregarIva', 'AgregarItem', 
                        'AgregarTributo', 'AgregarCmpAsoc', 'EstablecerCampoItem', 
                        'AutorizarComprobante', 'CAESolicitar', 
                        'SolicitarCAEA', 'ConsultarCAEA', 'ConsultarCAEAEntreFechas', 
                        'InformarComprobanteCAEA', 
                        'InformarCAEANoUtilizado', 'InformarCAEANoUtilizadoPtoVta',
                        'ConsultarUltimoComprobanteAutorizado', 'CompUltimoAutorizado', 
                        'ConsultarPtosVtaCAEANoInformados',
                        'ConsultarComprobante',
                        'ConsultarTiposComprobante', 
                        'ConsultarTiposDocumento',
                        'ConsultarAlicuotasIVA',
                        'ConsultarCondicionesIVA',
                        'ConsultarMonedas',
                        'ConsultarUnidadesMedida',
                        'ConsultarTiposTributo',
                        'ConsultarCotizacionMoneda',
                        'ConsultarPuntosVentaCAE',
                        'ConsultarPuntosVentaCAEA',
                        'AnalizarXml', 'ObtenerTagXml',
                        'Dummy', 'Conectar', 'DebugLog']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir',  
        'Resultado', 'Obs', 'Observaciones', 'ErrCode', 'ErrMsg',
        'EmisionTipo', 'Reproceso', 'Reprocesar',
        'CAE','Vencimiento', 'Evento', 'Errores', 'Traceback', 'Excepcion',
        'CAEA', 'Periodo', 'Orden', 'FchVigDesde', 'FchVigHasta', 'FchTopeInf', 'FchProceso',
        'CbteNro', 'FechaCbte', 'PuntoVenta', 'ImpTotal']
        
    _reg_progid_ = "WSMTXCA"
    _reg_clsid_ = "{8128E6AB-FB22-4952-8EA6-BD41C29B17CA}"

    Version = "%s %s" % (__version__, HOMO and 'Homologaci�n' or '')
    
    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.CAEA = None
        self.Periodo = self.Orden = ""
        self.FchVigDesde = self.FchVigHasta = ""
        self.FchTopeInf = self.FchProceso = ""
        self.client = None
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ErrCode = self.ErrMsg = self.Traceback = self.Excepcion = ""
        self.EmisionTipo = '' 
        self.Reprocesar = self.Reproceso = '' # no implementado
        self.Log = None
        self.InstallDir = INSTALL_DIR

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))
            self.ErrMsg = '\n'.join(self.Errores)
                   
    def __log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')

    def DebugLog(self):
        "Devolver y limpiar la bit�cora de depuraci�n"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg    

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None):
        # cliente soap del web service
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = WSMTXCA.Version + " " + Http._wrapper_version
        proxy_dict = parse_proxy(proxy)
        if HOMO or not wsdl:
            wsdl = WSDL
        if not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
            wsdl += "?wsdl"
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.__log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            ns='ser',
            trace = "--trace" in sys.argv)
        return True

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.dummy()
        self.AppServerStatus = result['appserver']
        self.DbServerStatus = result['dbserver']
        self.AuthServerStatus = result['authserver']
        return True

    def CrearFactura(self, concepto=None, tipo_doc=None, nro_doc=None, tipo_cbte=None, punto_vta=None,
            cbt_desde=None, cbt_hasta=None, imp_total=None, imp_tot_conc=None, imp_neto=None,
            imp_subtotal=None, imp_trib=None, imp_op_ex=None, fecha_cbte=None, fecha_venc_pago=None, 
            fecha_serv_desde=None, fecha_serv_hasta=None, #--
            moneda_id=None, moneda_ctz=None, observaciones=None, caea=None, fch_venc_cae=None,
            **kwargs
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportaci�n 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto,
                'imp_subtotal': imp_subtotal, # 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'observaciones': observaciones,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
                'detalles': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        if caea: fact['caea'] = caea
        if fch_venc_cae: fact['fch_venc_cae'] = fch_venc_cae
        
        self.factura = fact
        return True

    def EstablecerCampoFactura(self, campo, valor):
        if campo in self.factura or campo in ('fecha_serv_desde', 'fecha_serv_hasta', 'caea', 'fch_venc_cae'):
            self.factura[campo] = valor
            return True
        else:
            return False

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwargs):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {
            'tipo': tipo, 
            'pto_vta': pto_vta, 
            'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id, desc, base_imp, alic, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        tributo = {
            'tributo_id': tributo_id, 
            'desc': desc, 
            'base_imp': base_imp, 
            'importe': importe,
            }
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id, base_imp, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        iva = { 
                'iva_id': iva_id, 
                'importe': importe,
              }
        self.factura['iva'].append(iva)
        return True

    def AgregarItem(self, u_mtx=None, cod_mtx=None, codigo=None, ds=None, qty=None, umed=None, precio=None, bonif=None, 
                    iva_id=None, imp_iva=None, imp_subtotal=None, **kwargs):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        umed = int(umed)
        if umed == 99:
            imp_subtotal = -abs(float(imp_subtotal))
            imp_iva = -abs(float(imp_iva))
        item = {
                'u_mtx': u_mtx,
                'cod_mtx': cod_mtx,
                'codigo': codigo,                
                'ds': ds,
                'qty': umed!=99 and qty or None,
                'umed': umed,
                'precio': umed!=99 and precio or None,
                'bonif': umed!=99 and bonif or None,
                'iva_id': iva_id,
                'imp_iva': imp_iva,
                'imp_subtotal': imp_subtotal,
                }
        self.factura['detalles'].append(item)
        return True

    def EstablecerCampoItem(self, campo, valor):
        if self.factura['detalles'] and campo in self.factura['detalles'][-1]:
            self.factura['detalles'][-1][campo] = valor
            return True
        else:
            return False

    
    @inicializar_y_capturar_excepciones
    def AutorizarComprobante(self):
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            'codigoTipoDocumento': f['tipo_doc'], 'numeroDocumento':f['nro_doc'],
            'codigoTipoComprobante': f['tipo_cbte'], 'numeroPuntoVenta': f['punto_vta'],
            'numeroComprobante': f['cbt_desde'], 'numeroComprobante': f['cbt_hasta'],
            'importeTotal': f['imp_total'], 'importeNoGravado': f['imp_tot_conc'],
            'importeGravado': f['imp_neto'],
            'importeSubtotal': f['imp_subtotal'], # 'imp_iva': imp_iva,
            'importeOtrosTributos': f['tributos']  and f['imp_trib'] or None, 
			'importeExento': f['imp_op_ex'],
            'fechaEmision': f['fecha_cbte'],
            'codigoMoneda': f['moneda_id'], 'cotizacionMoneda': f['moneda_ctz'],
            'codigoConcepto': f['concepto'],
            'observaciones': f['observaciones'],
            'fechaVencimientoPago': f.get('fecha_venc_pago'),
            'fechaServicioDesde': f.get('fecha_serv_desde'),
            'fechaServicioHasta': f.get('fecha_serv_hasta'),
            'arrayComprobantesAsociados': f['cbtes_asoc'] and [{'comprobanteAsociado': {
                'codigoTipoComprobante': cbte_asoc['tipo'], 
                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                'numeroComprobante': cbte_asoc['nro'],
                }} for cbte_asoc in f['cbtes_asoc']] or None,
            'arrayOtrosTributos': f['tributos'] and [ {'otroTributo': {
                'codigo': tributo['tributo_id'], 
                'descripcion': tributo['desc'], 
                'baseImponible': tributo['base_imp'], 
                'importe': tributo['importe'],
                }} for tributo in f['tributos']] or None,
            'arraySubtotalesIVA': f['iva'] and [{'subtotalIVA': { 
                'codigo': iva['iva_id'], 
                'importe': iva['importe'],
                }} for iva in f['iva']] or None,
            'arrayItems': f['detalles'] and [{'item':{
                'unidadesMtx': it['u_mtx'],
                'codigoMtx': it['cod_mtx'],
                'codigo': it['codigo'],                
                'descripcion': it['ds'],
                'cantidad': it['qty'],
                'codigoUnidadMedida': it['umed'],
                'precioUnitario': it['precio'],
                'importeBonificacion': it['bonif'],
                'codigoCondicionIVA': it['iva_id'],
                'importeIVA': it['imp_iva'] if int(f['tipo_cbte']) not in (6, 7, 8) and it['imp_iva'] is not None else None,
                'importeItem': it['imp_subtotal'],
                }} for it in f['detalles']] or None,
            }
                
        ret = self.client.autorizarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            comprobanteCAERequest = fact,
            )
        
        # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
        if self.Reprocesar and ('arrayErrores' in ret):
            for error in ret['arrayErrores']:
                err_code = error['codigoDescripcion']['codigo']
                if ret['resultado'] == 'R' and err_code == 102:
                    # guardo los mensajes xml originales
                    xml_request = self.client.xml_request
                    xml_response = self.client.xml_response
                    cae = self.ConsultarComprobante(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                    if cae and self.EmisionTipo=='CAE':
                        self.Reproceso = 'S'
                        self.Resultado = 'A'  # verificar O
                        return cae
                    self.Reproceso = 'N'
                    # reestablesco los mensajes xml originales
                    self.client.xml_request = xml_request
                    self.client.xml_response = xml_response
                    
        self.Resultado = ret['resultado'] # u'A'
        self.Errores = []
        if ret['resultado'] in ("A", "O"):
            cbteresp = ret['comprobanteResponse']
            self.FechaCbte = cbteresp['fechaEmision'].strftime("%Y/%m/%d")
            self.CbteNro = cbteresp['numeroComprobante'] # 1L
            self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
            #self. = cbteresp['cuit'] # 20267565393L
            #self. = cbteresp['codigoTipoComprobante'] 
            self.Vencimiento = cbteresp['fechaVencimientoCAE'].strftime("%Y/%m/%d")
            self.CAE = str(cbteresp['CAE']) # 60423794871430L
        self.__analizar_errores(ret)
        
        for error in ret.get('arrayObservaciones', []):
            self.Observaciones.append("%(codigo)s: %(descripcion)s" % (
                error['codigoDescripcion']))
        self.Obs = '\n'.join(self.Observaciones)

        if 'evento' in ret:
            self.Evento = '%(codigo)s: %(descripcion)s' % ret['evento']
        return self.CAE
    
    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        try:
            cae = self.AutorizarComprobante() or ''
            self.Excepcion = "OK!"
        except:
            cae = "ERR"
        finally:
            return cae

    @inicializar_y_capturar_excepciones
    def SolicitarCAEA(self, periodo, orden):
        
        ret = self.client.solicitarCAEA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            solicitudCAEA = {
                'periodo': periodo,
                'orden': orden},
        )
        
        self.__analizar_errores(ret)
                    
        if 'CAEAResponse' in ret:
            res = ret['CAEAResponse']
            self.CAEA = res['CAEA']
            self.Periodo = res['periodo']
            self.Orden = res['orden']
            self.FchVigDesde = res['fechaDesde']
            self.FchVigHasta = res['fechaHasta']
            self.FchTopeInf = res['fechaTopeInforme']
            self.FchProceso = res['fechaProceso']
        return self.CAEA and str(self.CAEA) or ''


    @inicializar_y_capturar_excepciones
    def ConsultarCAEA(self, periodo=None, orden=None, caea=None):
        "M�todo de consulta de CAEA"
        if periodo and orden:
            anio, mes = int(periodo[0:4]), int(periodo[4:6])
            if int(orden)==1:
                dias = 1, 15
            else:
                if mes in (1,3,5,7,8,10,12):
                    dias = 16, 31
                elif mes in (4,6,9,11):
                    dias = 16, 30
                else:
                    import calendar
                    if calendar.isleap(anio):
                        dias = 16, 29 # biciesto
                    else:
                        dias = 16, 28

            fecha_desde = "%04d-%02d-%02d" % (anio, mes, dias[0])
            fecha_hasta = "%04d-%02d-%02d" % (anio, mes, dias[1])

            caeas = self.ConsultarCAEAEntreFechas(fecha_desde, fecha_hasta)
            if caeas:
                caea = caeas[0]
        
        if caea:
            ret = self.client.consultarCAEA(
                authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
                CAEA = caea,
            )

            self.__analizar_errores(ret)

            if 'CAEAResponse' in ret:
                res = ret['CAEAResponse']
                self.CAEA = res['CAEA']
                self.Periodo = res['periodo']
                self.Orden = res['orden']
                self.FchVigDesde = res['fechaDesde']
                self.FchVigHasta = res['fechaHasta']
                self.FchTopeInf = res['fechaTopeInforme']
                self.FchProceso = res['fechaProceso']
        return self.CAEA and str(self.CAEA) or ''


    @inicializar_y_capturar_excepciones
    def ConsultarCAEAEntreFechas(self, fecha_desde, fecha_hasta):
        "M�todo de consulta de CAEA"

        ret = self.client.consultarCAEAEntreFechas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            fechaDesde = fecha_desde,
            fechaHasta = fecha_hasta,
        )
                
        self.__analizar_errores(ret)

        caeas = []
        if 'arrayCAEAResponse' in ret:
            return [res['CAEAResponse']['CAEA'] for res in ret['arrayCAEAResponse']]
        return []

    @inicializar_y_capturar_excepciones
    def InformarComprobanteCAEA(self):
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            'codigoTipoDocumento': f['tipo_doc'], 'numeroDocumento':f['nro_doc'],
            'codigoTipoComprobante': f['tipo_cbte'], 'numeroPuntoVenta': f['punto_vta'],
            'numeroComprobante': f['cbt_desde'], 'numeroComprobante': f['cbt_hasta'],
            'codigoTipoAutorizacion': 'A',
            'codigoAutorizacion': f['caea'],
            'importeTotal': f['imp_total'], 'importeNoGravado': f['imp_tot_conc'],
            'importeGravado': f['imp_neto'],
            'importeSubtotal': f['imp_subtotal'], # 'imp_iva': imp_iva,
            'importeOtrosTributos': f['tributos'] and f['imp_trib'] or None, 
			'importeExento': f['imp_op_ex'],
            'fechaEmision': f['fecha_cbte'],
            'codigoMoneda': f['moneda_id'], 'cotizacionMoneda': f['moneda_ctz'],
            'codigoConcepto': f['concepto'],
            'observaciones': f['observaciones'],
            'fechaVencimientoPago': f.get('fecha_venc_pago'),
            'fechaServicioDesde': f.get('fecha_serv_desde'),
            'fechaServicioHasta': f.get('fecha_serv_hasta'),
            'arrayComprobantesAsociados': f['cbtes_asoc'] and [{'comprobanteAsociado': {
                'codigoTipoComprobante': cbte_asoc['tipo'], 
                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                'numeroComprobante': cbte_asoc['nro'],
                }} for cbte_asoc in f['cbtes_asoc']] or None,
            'arrayOtrosTributos': f['tributos'] and [{'otroTributo': {
                'codigo': tributo['tributo_id'], 
                'descripcion': tributo['desc'], 
                'baseImponible': tributo['base_imp'], 
                'importe': tributo['importe'],
                }} for tributo in f['tributos']] or None,
            'arraySubtotalesIVA': f['iva'] and [{'subtotalIVA': { 
                'codigo': iva['iva_id'], 
                'importe': iva['importe'],
                }} for iva in f['iva']] or None,
            'arrayItems': f['detalles'] and [{'item':{
                'unidadesMtx': it['u_mtx'],
                'codigoMtx': it['cod_mtx'],
                'codigo': it['codigo'],                
                'descripcion': it['ds'],
                'cantidad': it['qty'],
                'codigoUnidadMedida': it['umed'],
                'precioUnitario': it['precio'],
                'importeBonificacion': it['bonif'],
                'codigoCondicionIVA': it['iva_id'],
                'importeIVA': it['imp_iva'] if int(f['tipo_cbte']) not in (6, 7, 8) and it['imp_iva'] is not None else None,
                'importeItem': it['imp_subtotal'],
                }} for it in f['detalles']] or None,
            }
                
        # fecha de vencimiento opcional (igual al �ltimo d�a de vigencia del CAEA)
        if 'fch_venc_cae' in f:
            fact['fechaVencimiento'] =  f['fch_venc_cae']

        ret = self.client.informarComprobanteCAEA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            comprobanteCAEARequest = fact,
            )
        
        self.Resultado = ret['resultado'] # u'A'
        self.Errores = []
        if ret['resultado'] in ("A", "O"):
            cbteresp = ret['comprobanteCAEAResponse']
            self.FchProceso = ret['fechaProceso'].strftime("%Y-%m-%d")
            self.CbteNro = cbteresp['numeroComprobante'] # 1L
            self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
            if 'fechaVencimientoCAE' in cbteresp:
                self.Vencimiento = cbteresp['fechaVencimientoCAE'].strftime("%Y-%m-%d")
            else:
                self.Vencimiento = ""
            self.CAEA = str(cbteresp['CAEA']) # 60423794871430L
            self.EmisionTipo = 'CAEA'
        self.__analizar_errores(ret)
        
        for error in ret.get('arrayObservaciones', []):
            self.Observaciones.append("%(codigo)s: %(descripcion)s" % (
                error['codigoDescripcion']))
        self.Obs = '\n'.join(self.Observaciones)

        if 'evento' in ret:
            self.Evento = '%(codigo)s: %(descripcion)s' % ret['evento']
        return self.CAEA


    @inicializar_y_capturar_excepciones
    def InformarCAEANoUtilizado(self, caea):
        ret = self.client.informarCAEANoUtilizado(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            CAEA=caea,
            )
        self.Resultado = ret['resultado'] # u'A'
        self.Errores = []
        if ret['resultado'] in ("A", "O"):
            self.FchProceso = ret['fechaProceso'].strftime("%Y-%m-%d")
            self.CAEA = str(ret['CAEA']) # 60423794871430L
            self.EmisionTipo = 'CAEA'
        self.__analizar_errores(ret)
        if 'evento' in ret:
            self.Evento = '%(codigo)s: %(descripcion)s' % ret['evento']
        return self.Resultado

    @inicializar_y_capturar_excepciones
    def InformarCAEANoUtilizadoPtoVta(self, caea, punto_vta):
        ret = self.client.informarCAEANoUtilizadoPtoVta(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            CAEA=caea,
            numeroPuntoVenta=punto_vta,
            )
        self.Resultado = ret['resultado'] # u'A'
        self.Errores = []
        if ret['resultado'] in ("A", "O"):
            self.FchProceso = ret['fechaProceso'].strftime("%Y-%m-%d")
            self.CAEA = str(ret['CAEA']) # 60423794871430L
            self.EmisionTipo = 'CAEA'
            self.PuntoVenta = ret['numeroPuntoVenta'] # 4000
        self.__analizar_errores(ret)
        if 'evento' in ret:
            self.Evento = '%(codigo)s: %(descripcion)s' % ret['evento']
        return self.Resultado

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoComprobanteAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.consultarUltimoComprobanteAutorizado(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            consultaUltimoComprobanteAutorizadoRequest = {
                'codigoTipoComprobante': tipo_cbte,
                'numeroPuntoVenta': punto_vta},
            )
        nro = ret.get('numeroComprobante')
        self.__analizar_errores(ret)
        self.CbteNro = nro
        return nro is not None and str(nro) or 0

    CompUltimoAutorizado = ConsultarUltimoComprobanteAutorizado

    @inicializar_y_capturar_excepciones
    def ConsultarComprobante(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        "Recuperar los datos completos de un comprobante ya autorizado"
        ret = self.client.consultarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            consultaComprobanteRequest = {
                'codigoTipoComprobante': tipo_cbte,
                'numeroPuntoVenta': punto_vta,
                'numeroComprobante': cbte_nro,
                },
            )
        # diferencias si hay reproceso:
        difs = []
        # analizo el resultado:
        if 'comprobante' in ret:
                cbteresp = ret['comprobante']
                if reproceso:
                    # verifico los campos registrados coincidan con los enviados:
                    f = self.factura
                    verificaciones = {
                        'codigoTipoComprobante': f['tipo_cbte'],
                        'numeroPuntoVenta': f['punto_vta'],
                        'codigoConcepto': f['concepto'],
                        'codigoTipoDocumento': f['tipo_doc'],
                        'numeroDocumento': f['nro_doc'],
                        'numeroComprobante': f['cbt_desde'],
                        'numeroComprobante': f['cbt_hasta'],
                        'fechaEmision': f['fecha_cbte'],
                        'importeTotal': decimal.Decimal(f['imp_total']),
                        'importeNoGravado': decimal.Decimal(f['imp_tot_conc']),
                        'importeGravado': decimal.Decimal(f['imp_neto']),
                        'importeExento': decimal.Decimal(f['imp_op_ex']),
                        'importeOtrosTributos': f['tributos'] and decimal.Decimal(f['imp_trib']) or None,
                        'importeSubtotal': f['imp_subtotal'],
                        'fechaServicioDesde': f.get('fecha_serv_desde'),
                        'fechaServicioHasta': f.get('fecha_serv_hasta'),
                        'fechaVencimientoPago': f.get('fecha_venc_pago'),
                        'codigoMoneda': f['moneda_id'],
                        'cotizacionMoneda': decimal.Decimal(f['moneda_ctz']),
                        'arrayItems': [
                            {'item': {
                                'unidadesMtx': it['u_mtx'],
                                'codigoMtx': it['cod_mtx'],
                                'codigo': it['codigo'],                
                                'descripcion': it['ds'],
                                'cantidad': it['qty'] and decimal.Decimal(it['qty']),
                                'codigoUnidadMedida': it['umed'],
                                'precioUnitario': it['precio'] and decimal.Decimal(it['precio']) or None,
                                #'importeBonificacion': it['bonif'],
                                'codigoCondicionIVA': decimal.Decimal(it['iva_id']),
                                'importeIVA': decimal.Decimal(it['imp_iva']) if int(f['tipo_cbte']) not in (6, 7, 8) and it['imp_iva'] is not None else None,
                                'importeItem': decimal.Decimal(it['imp_subtotal']),
                                }}
                            for it in f['detalles']],
                        'arrayComprobantesAsociados': [
                            {'comprobanteAsociado': {
                                'codigoTipoComprobante': cbte_asoc['tipo'],
                                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                                'numeroComprobante': cbte_asoc['nro']}}
                            for cbte_asoc in f['cbtes_asoc']],
                        'arrayOtrosTributos': [
                            {'otroTributo': {
                                'codigo': tributo['tributo_id'], 
                                'descripcion': tributo['desc'],
                                'baseImponible': decimal.Decimal(tributo['base_imp']),
                                'importe': decimal.Decimal(tributo['importe']),
                                }}
                            for tributo in f['tributos']],
                        'arraySubtotalesIVA': [ 
                            {'subtotalIVA': {
                                'codigo': iva['iva_id'],
                                'importe': decimal.Decimal(iva['importe']),
                                }}
                            for iva in f['iva']],
                        }
                    verifica(verificaciones, cbteresp, difs)
                    if difs:
                        print "Diferencias:", difs
                        self.__log("Diferencias: %s" % difs)
                self.FechaCbte = cbteresp['fechaEmision'].strftime("%Y/%m/%d")
                self.CbteNro = cbteresp['numeroComprobante'] # 1L
                self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
                self.Vencimiento = cbteresp['fechaVencimiento'].strftime("%Y/%m/%d")
                self.ImpTotal = str(cbteresp['importeTotal'])
                self.CAE = str(cbteresp['codigoAutorizacion']) # 60423794871430L
                self.EmisionTipo =  cbteresp['codigoTipoAutorizacion']=='A' and 'CAEA' or 'CAE'
        self.__analizar_errores(ret)
        if not difs:
            return self.CAE


    @inicializar_y_capturar_excepciones
    def ConsultarTiposComprobante(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposComprobante']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDocumento(self):
        ret = self.client.consultarTiposDocumento(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposDocumento']]

    @inicializar_y_capturar_excepciones
    def ConsultarAlicuotasIVA(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarAlicuotasIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayAlicuotasIVA']]

    @inicializar_y_capturar_excepciones
    def ConsultarCondicionesIVA(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCondicionesIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayCondicionesIVA']]
    @inicializar_y_capturar_excepciones
    def ConsultarMonedas(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarMonedas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayMonedas']]

    @inicializar_y_capturar_excepciones
    def ConsultarUnidadesMedida(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarUnidadesMedida(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayUnidadesMedida']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposTributo(self):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposTributo(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposTributo']]

    @inicializar_y_capturar_excepciones
    def ConsultarCotizacionMoneda(self, moneda_id):
        "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCotizacionMoneda(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoMoneda=moneda_id,
            )
        self.__analizar_errores(ret)
        if 'cotizacionMoneda' in ret:
            return str(ret['cotizacionMoneda'])

    @inicializar_y_capturar_excepciones
    def ConsultarPuntosVentaCAE(self):
        "Este m�todo permite consultar los puntos de venta habilitados para CAE en este WS"
        ret = self.client.consultarPuntosVentaCAE(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s" % p
                 for p in ret['arrayPuntosVenta']]

    @inicializar_y_capturar_excepciones
    def ConsultarPuntosVentaCAEA(self):
        "Este m�todo permite consultar los puntos de venta habilitados para CAEA en este WS"
        ret = self.client.consultarPuntosVentaCAEA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s" % p
                 for p in ret['arrayPuntosVenta']]

    @inicializar_y_capturar_excepciones
    def ConsultarPtosVtaCAEANoInformados(self, caea):
        "Este m�todo permite  consultar que puntos de venta a�n no fueron informados para  un  CAEA determinado."
        ret = self.client.consultarPtosVtaCAEANoInformados(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            CAEA=caea,
            )
        return [" ".join([("%s=%s" % (k, v)) for k, v in p['puntoVenta'].items()])
                 for p in ret['arrayPuntosVenta']]

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = u"%s" % (e)
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posici�n
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = u"%s" % (e)


def main():
    "Funci�n principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    # obteniendo el TA
    TA = "TA-wsmtxca.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsmtxca")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        ta_string = wsaa.call_wsaa(cms, trace='--trace' in sys.argv)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA

    wsmtxca = WSMTXCA()
    wsmtxca.Cuit = "20267565393"
    wsmtxca.Token = str(ta.credentials.token)
    wsmtxca.Sign = str(ta.credentials.sign)

    wsmtxca.Conectar()
    
    if "--dummy" in sys.argv:
        print wsmtxca.client.help("dummy")
        wsmtxca.Dummy()
        print "AppServerStatus", wsmtxca.AppServerStatus
        print "DbServerStatus", wsmtxca.DbServerStatus
        print "AuthServerStatus", wsmtxca.AuthServerStatus
    
    if "--prueba" in sys.argv:
        print wsmtxca.client.help("autorizarComprobante").encode("latin1")
        try:
            tipo_cbte = 1
            punto_vta = 4000
            cbte_nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "30000000007"
            cbte_nro = long(cbte_nro) + 1
            cbt_desde = cbte_nro; cbt_hasta = cbt_desde
            imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_trib = "1.00"; imp_op_ex = "0.00"; imp_subtotal = "100.00"
            fecha_cbte = fecha; fecha_venc_pago = fecha
            # Fechas del per�odo del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs = "Observaciones Comerciales, libre"

            wsmtxca.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, #--
                moneda_id, moneda_ctz, obs)
            
            #tipo = 19
            #pto_vta = 2
            #nro = 1234
            #wsmtxca.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_im = 100
            importe = 21
            wsmtxca.AgregarIva(iva_id, base_imp, importe)
            
            u_mtx = 123456
            cod_mtx = 1234567890123
            codigo = "P0001"
            ds = "Descripcion del producto P0001"
            qty = 2.00
            umed = 7
            precio = 100.00
            bonif = 0.00
            iva_id = 5
            imp_iva = 42.00
            imp_subtotal = 242.00
            wsmtxca.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                        iva_id, imp_iva, imp_subtotal)
            
            wsmtxca.AgregarItem(None, None, None, 'bonificacion', 0, 99, 1, None, 
                        5, -21, -121)
            
            wsmtxca.AutorizarComprobante()

            print "Resultado", wsmtxca.Resultado
            print "CAE", wsmtxca.CAE
            print "Vencimiento", wsmtxca.Vencimiento
            
            cae = wsmtxca.CAE
            
            wsmtxca.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
            print "CAE consulta", wsmtxca.CAE, wsmtxca.CAE==cae 
            print "NRO consulta", wsmtxca.CbteNro, wsmtxca.CbteNro==cbte_nro 
            print "TOTAL consulta", wsmtxca.ImpTotal, wsmtxca.ImpTotal==imp_total

            wsmtxca.AnalizarXml("XmlResponse")
            assert wsmtxca.ObtenerTagXml('codigoAutorizacion') == str(wsmtxca.CAE)
            assert wsmtxca.ObtenerTagXml('codigoConcepto') == str(concepto)
            assert wsmtxca.ObtenerTagXml('arrayItems', 0, 'item', 'unidadesMtx') == '123456'


        except:
            print wsmtxca.XmlRequest        
            print wsmtxca.XmlResponse        
            print wsmtxca.ErrCode
            print wsmtxca.ErrMsg


    if "--parametros" in sys.argv:
        print wsmtxca.ConsultarTiposComprobante()
        print wsmtxca.ConsultarTiposDocumento()
        print wsmtxca.ConsultarAlicuotasIVA()
        print wsmtxca.ConsultarCondicionesIVA()
        print wsmtxca.ConsultarMonedas()
        print wsmtxca.ConsultarUnidadesMedida()
        print wsmtxca.ConsultarTiposTributo()

    if "--cotizacion" in sys.argv:
        print wsmtxca.ConsultarCotizacionMoneda('DOL')
        
    if "--solicitar-caea" in sys.argv:
        periodo = sys.argv[sys.argv.index("--solicitar-caea")+1]
        orden = sys.argv[sys.argv.index("--solicitar-caea")+2]

        if DEBUG: 
            print "Consultando CAEA para periodo %s orden %s" % (periodo, orden)
        
        caea = wsmtxca.ConsultarCAEA(periodo, orden)
        if not caea:
            print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
            caea = wsmtxca.SolicitarCAEA(periodo, orden)

        print "CAEA:", caea

        if wsmtxca.Errores:
            print "Errores:"
            for error in wsmtxca.Errores:
                print error
            
        if DEBUG:
            print "periodo:", wsmtxca.Periodo 
            print "orden:", wsmtxca.Orden 
            print "fch_vig_desde:", wsmtxca.FchVigDesde 
            print "fch_vig_hasta:", wsmtxca.FchVigHasta 
            print "fch_tope_inf:", wsmtxca.FchTopeInf 
            print "fch_proceso:", wsmtxca.FchProceso
        

# busco el directorio de instalaci�n (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))

if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSMTXCA)
    else:
        main()
