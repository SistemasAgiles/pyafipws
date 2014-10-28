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
WSFEv1 de AFIP (Factura Electr�nica Nacional - Version 1 - RG2904 opci�n B)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2014 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.15c"

import datetime
import decimal
import os
import sys
from utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir

HOMO = False                    # solo homologaci�n
TYPELIB = False                 # usar librer�a de tipos (TLB)
LANZAR_EXCEPCIONES = False      # valor por defecto: True

#WSDL = "https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
#WSDL = "file:///home/reingart/tmp/service.asmx.xml"


class WSFEv1(BaseWS):
    "Interfaz para el WebService de Factura Electr�nica Version 1"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'CAESolicitar', 
                        'AgregarTributo', 'AgregarCmpAsoc', 'AgregarOpcional',
                        'CompUltimoAutorizado', 'CompConsultar',
                        'CAEASolicitar', 'CAEAConsultar', 'CAEARegInformativo',
                        'CAEASinMovimientoInformar',
                        'ParamGetTiposCbte',
                        'ParamGetTiposConcepto',
                        'ParamGetTiposDoc',
                        'ParamGetTiposIva',
                        'ParamGetTiposMonedas',
                        'ParamGetTiposOpcional',
                        'ParamGetTiposTributos',
                        'ParamGetCotizacion', 
                        'ParamGetPtosVenta',
                        'AnalizarXml', 'ObtenerTagXml',
                        'SetParametros',
                        'Dummy', 'Conectar', 'DebugLog']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'Excepcion', 'LanzarExcepciones',
        'Resultado', 'Obs', 'Observaciones', 'Traceback', 'InstallDir',
        'CAE','Vencimiento', 'Eventos', 'Errores', 'ErrCode', 'ErrMsg',
        'Reprocesar', 'Reproceso', 'EmisionTipo', 'CAEA',
        'CbteNro', 'CbtDesde', 'CbtHasta', 'FechaCbte', 
        'ImpTotal', 'ImpNeto', 'ImptoLiq', 'ImpOpEx'
        'ImpIVA', 'ImpOpEx', 'ImpTrib',]
        
    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{CA0E604D-E3D7-493A-8880-F6CDD604185E}"

    if TYPELIB:
        _typelib_guid_ = '{B1D7283C-3EC2-463E-89B4-11F5228E2A15}'
        _typelib_version_ = 1, 13
        _com_interfaces_ = ['IWSFEv1']
        ##_reg_class_spec_ = "wsfev1.WSFEv1"
        
    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologaci�n' or '')
    Reprocesar = True   # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None
    
    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.CAEA = self.Vencimiento = ''
        self.CbteNro = self.CbtDesde = self.CbtHasta = self.PuntoVenta = None
        self.ImpTotal = self.ImpIVA = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
        self.EmisionTipo = self.Periodo = self.Orden = ""
        self.FechaCbte = self.FchVigDesde = self.FchVigHasta = self.FchTopeInf = self.FchProceso = ""
        
    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                    ))
            self.ErrCode = ' '.join([str(error['Err']['Code']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)
        if 'Events' in ret:
            events = ret['Events']
            self.Eventos = ['%s: %s' % (evt['code'], evt['msg']) for evt in events]

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEDummy()['FEDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']
        return True

    def CrearFactura(self, concepto=1, tipo_doc=80, nro_doc="", tipo_cbte=1, punto_vta=0,
            cbt_desde=0, cbt_hasta=0, imp_total=0.00, imp_tot_conc=0.00, imp_neto=0.00,
            imp_iva=0.00, imp_trib=0.00, imp_op_ex=0.00, fecha_cbte="", fecha_venc_pago="", 
            fecha_serv_desde=None, fecha_serv_hasta=None, #--
            moneda_id="PES", moneda_ctz="1.0000", caea=None, **kwargs
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportaci�n 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto, 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
                'opcionales': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        if caea: fact['caea'] = caea

        self.factura = fact
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwarg):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'tipo': tipo, 'pto_vta': pto_vta, 'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg):
        "Agrego un tributo a una factura (interna)"
        tributo = { 'tributo_id': tributo_id, 'desc': desc, 'base_imp': base_imp, 
                    'alic': alic, 'importe': importe}
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = { 'iva_id': iva_id, 'base_imp': base_imp, 'importe': importe }
        self.factura['iva'].append(iva)
        return True

    def AgregarOpcional(self, opcional_id=0, valor="", **kwarg):
        "Agrego un dato opcional a una factura (interna)"
        op = { 'opcional_id': opcional_id, 'valor': valor }
        self.factura['opcionales'].append(op)
        return True

    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': f['cbtes_asoc'] and [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']] or None,
                    'Tributos': f['tributos'] and [
                        {'Tributo': {
                            'Id': tributo['tributo_id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']] or None,
                    'Iva': f['iva'] and [ 
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']] or None,
                    'Opcionales': [ 
                        {'Opcional': {
                            'Id': opcional['opcional_id'],
                            'Valor': opcional['valor'],
                            }} for opcional in f['opcionales']] or None,
                    }
                }]
            })
        
        result = ret['FECAESolicitarResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and ('Errors' in result or 'Observaciones' in fedetresp):
                for error in result.get('Errors',[])+fedetresp.get('Observaciones',[]):
                    err_code = str(error.get('Err', error.get('Obs'))['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='10016':
                        # guardo los mensajes xml originales
                        xml_request = self.client.xml_request
                        xml_response = self.client.xml_response
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo=='CAE':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'
                        # reestablesco los mensajes xml originales
                        self.client.xml_request = xml_request
                        self.client.xml_response = xml_response
                        
            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp.get('CbteFch', "") #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp.get('CbteHasta', 0) # 1L
            self.PuntoVenta = fecabresp.get('PtoVta', 0) # 4000
            self.CbtDesde =fedetresp.get('CbteDesde', 0)
            self.CbtHasta = fedetresp.get('CbteHasta', 0)
        self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CompTotXRequest(self):
        ret = self.client.FECompTotXRequest (
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        
        result = ret['FECompTotXRequestResult']
        return result['RegXReq']

    @inicializar_y_capturar_excepciones
    def CompUltimoAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.FECompUltimoAutorizado(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta,
            CbteTipo=tipo_cbte,
            )
        
        result = ret['FECompUltimoAutorizadoResult']
        self.CbteNro = result['CbteNro']        
        self.__analizar_errores(result)
        return self.CbteNro is not None and str(self.CbteNro) or ''

    @inicializar_y_capturar_excepciones
    def CompConsultar(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        difs = [] # si hay reproceso, verifico las diferencias con AFIP

        ret = self.client.FECompConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCompConsReq={
                'CbteTipo': tipo_cbte,
                'CbteNro': cbte_nro,
                'PtoVta': punto_vta,
            })
        
        result = ret['FECompConsultarResult']
        if 'ResultGet' in result:
            resultget = result['ResultGet']
            
            if reproceso:
                # verifico los campos registrados coincidan con los enviados:
                f = self.factura
                verificaciones = {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'] and float(f['imp_total']) or 0.0,
                    'ImpTotConc': f['imp_tot_conc'] and float(f['imp_tot_conc']) or 0.0,
                    'ImpNeto': f['imp_neto'] and float(f['imp_neto']) or 0.0,
                    'ImpOpEx': f['imp_op_ex'] and float(f['imp_op_ex']) or 0.0,
                    'ImpTrib': f['imp_trib'] and float(f['imp_trib']) or 0.0,
                    'ImpIVA': f['imp_iva'] and float(f['imp_iva']) or 0.0,
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': float(f['moneda_ctz']),
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': float(tributo['base_imp']),
                            'Alic': float(tributo['alic']),
                            'Importe': float(tributo['importe']),
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': float(iva['base_imp']),
                            'Importe': float(iva['importe']),
                            }}
                        for iva in f['iva']],
                    }
                verifica(verificaciones, resultget.copy(), difs)
                if difs:
                    print "Diferencias:", difs
                    self.log("Diferencias: %s" % difs)
            self.FechaCbte = resultget['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = resultget['CbteHasta'] # 1L
            self.PuntoVenta = resultget['PtoVta'] # 4000
            self.Vencimiento = resultget['FchVto'] #.strftime("%Y/%m/%d")
            self.ImpTotal = str(resultget['ImpTotal'])
            cod_aut = resultget['CodAutorizacion'] and str(resultget['CodAutorizacion']) or ''# 60423794871430L
            self.Resultado = resultget['Resultado']
            self.CbtDesde =resultget['CbteDesde']
            self.CbtHasta = resultget['CbteHasta']
            self.ImpTotal = resultget['ImpTotal']
            self.ImpNeto = resultget['ImpNeto']
            self.ImptoLiq = self.ImpIVA = resultget['ImpIVA']
            self.ImpOpEx = resultget['ImpOpEx']
            self.ImpTrib = resultget['ImpTrib']
            self.EmisionTipo = resultget['EmisionTipo']
            if self.EmisionTipo=='CAE':
                self.CAE = cod_aut
            elif self.EmisionTipo=='CAEA':
                self.CAEA = cod_aut

        self.__analizar_errores(result)
        if not difs:
            return self.CAE or self.CAEA
        else:
            return ''


    @inicializar_y_capturar_excepciones
    def CAESolicitarLote(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEReq={
                'FeCabReq': {'CantReg': 250, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde']+k,
                    'CbteHasta': f['cbt_hasta']+k,
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    'Opcionales': [ 
                        {'Opcional': {
                            'Id': opcional['opcional_id'],
                            'Valor': opcional['valor'],
                            }} for opcional in f['opcionales']] or None,
                    }
                } for k in range (250)]
            })
        
        result = ret['FECAESolicitarResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEDetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='10016':
                        cae = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if cae and self.EmisionTipo=='CAEA':
                            self.Reproceso = 'S'
                            return cae
                        self.Reproceso = 'N'
            
            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAE = fedetresp['CAE'] and str(fedetresp['CAE']) or ""
            self.EmisionTipo = 'CAE'
            self.Vencimiento = fedetresp['CAEFchVto']
            self.FechaCbte = fedetresp['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta'] # 1L
            self.PuntoVenta = fecabresp['PtoVta'] # 4000
            self.CbtDesde =fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAE


    @inicializar_y_capturar_excepciones
    def CAEASolicitar(self, periodo, orden):
        ret = self.client.FECAEASolicitar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo, 
            Orden=orden,
            )
        
        result = ret['FECAEASolicitarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''


    @inicializar_y_capturar_excepciones
    def CAEAConsultar(self, periodo, orden):
        "M�todo de consulta de CAEA"
        ret = self.client.FECAEAConsultar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            Periodo=periodo, 
            Orden=orden,
            )
        
        result = ret['FECAEAConsultarResult']
        self.__analizar_errores(result)

        if 'ResultGet' in result:
            result = result['ResultGet']
            if 'CAEA' in result:
                self.CAEA = result['CAEA']
                self.Periodo = result['Periodo']
                self.Orden = result['Orden']
                self.FchVigDesde = result['FchVigDesde']
                self.FchVigHasta = result['FchVigHasta']
                self.FchTopeInf = result['FchTopeInf']
                self.FchProceso = result['FchProceso']

        return self.CAEA and str(self.CAEA) or ''
    
    @inicializar_y_capturar_excepciones
    def CAEARegInformativo(self):
        "M�todo para informar comprobantes emitidos con CAEA"
        f = self.factura
        ret = self.client.FECAEARegInformativo(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            FeCAEARegInfReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': f['punto_vta'], 
                    'CbteTipo': f['tipo_cbte']},
                'FeDetReq': [{'FECAEADetRequest': {
                    'Concepto': f['concepto'],
                    'DocTipo': f['tipo_doc'],
                    'DocNro': f['nro_doc'],
                    'CbteDesde': f['cbt_desde'],
                    'CbteHasta': f['cbt_hasta'],
                    'CbteFch': f['fecha_cbte'],
                    'ImpTotal': f['imp_total'],
                    'ImpTotConc': f['imp_tot_conc'],
                    'ImpNeto': f['imp_neto'],
                    'ImpOpEx': f['imp_op_ex'],
                    'ImpTrib': f['imp_trib'],
                    'ImpIVA': f['imp_iva'],
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f.get('fecha_venc_pago'),
                    'FchServDesde': f.get('fecha_serv_desde'),
                    'FchServHasta': f.get('fecha_serv_hasta'),
                    'FchVtoPago': f['fecha_venc_pago'],
                    'MonId': f['moneda_id'],
                    'MonCotiz': f['moneda_ctz'],                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc['tipo'],
                            'PtoVta': cbte_asoc['pto_vta'], 
                            'Nro': cbte_asoc['nro']}}
                        for cbte_asoc in f['cbtes_asoc']],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo['tributo_id'], 
                            'Desc': tributo['desc'],
                            'BaseImp': tributo['base_imp'],
                            'Alic': tributo['alic'],
                            'Importe': tributo['importe'],
                            }}
                        for tributo in f['tributos']],
                    'Iva': [ 
                        {'AlicIva': {
                            'Id': iva['iva_id'],
                            'BaseImp': iva['base_imp'],
                            'Importe': iva['importe'],
                            }}
                        for iva in f['iva']],
                    'CAEA': f['caea'],
                    }
                }]
            })
        
        result = ret['FECAEARegInformativoResult']
        if 'FeCabResp' in result:
            fecabresp = result['FeCabResp']
            fedetresp = result['FeDetResp'][0]['FECAEADetResponse']
            
            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and 'Errors' in result:
                for error in result['Errors']:
                    err_code = str(error['Err']['Code'])
                    if fedetresp['Resultado']=='R' and err_code=='703':
                        caea = self.CompConsultar(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                        if caea and self.EmisionTipo=='CAE':
                            self.Reproceso = 'S'
                            return caea
                        self.Reproceso = 'N'

            self.Resultado = fecabresp['Resultado']
            # Obs:
            for obs in fedetresp.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.CAEA = fedetresp['CAEA'] and str(fedetresp['CAEA']) or ""
            self.EmisionTipo = 'CAEA'
            self.FechaCbte = fedetresp['CbteFch'] #.strftime("%Y/%m/%d")
            self.CbteNro = fedetresp['CbteHasta'] # 1L
            self.PuntoVenta = fecabresp['PtoVta'] # 4000
            self.CbtDesde =fedetresp['CbteDesde']
            self.CbtHasta = fedetresp['CbteHasta']
            self.__analizar_errores(result)
        return self.CAEA

    @inicializar_y_capturar_excepciones
    def CAEASinMovimientoInformar(self, punto_vta, caea):
        "M�todo  para informar CAEA sin movimiento"
        ret = self.client.FECAEASinMovimientoInformar(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            PtoVta=punto_vta, 
            CAEA=caea,
            )
        
        result = ret['FECAEASinMovimientoInformarResult']
        self.__analizar_errores(result)

        if 'CAEA' in result:
            self.CAEA = result['CAEA']
        if 'FchProceso' in result:
            self.FchProceso = result['FchProceso']
        if 'Resultado' in result:
            self.Resultado = result['Resultado']
            self.PuntoVenta = result['PtoVta'] # 4000

        return self.Resultado or ''
    
    @inicializar_y_capturar_excepciones
    def ParamGetTiposCbte(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de Comprobantes"
        ret = self.client.FEParamGetTiposCbte(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposCbteResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['CbteTipo']).replace("\t", sep)
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposConcepto(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de Conceptos"
        ret = self.client.FEParamGetTiposConcepto(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposConceptoResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['ConceptoTipo']).replace("\t", sep)
                 for p in res['ResultGet']]
                

    @inicializar_y_capturar_excepciones
    def ParamGetTiposDoc(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de Documentos"
        ret = self.client.FEParamGetTiposDoc(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposDocResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['DocTipo']).replace("\t", sep)
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposIva(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de Al�cuotas"
        ret = self.client.FEParamGetTiposIva(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposIvaResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['IvaTipo']).replace("\t", sep)
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposMonedas(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Monedas"
        ret = self.client.FEParamGetTiposMonedas(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposMonedasResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['Moneda']).replace("\t", sep)
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposOpcional(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de datos opcionales"
        ret = self.client.FEParamGetTiposOpcional(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposOpcionalResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['OpcionalTipo']).replace("\t", sep)
                 for p in res.get('ResultGet', [])]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposTributos(self, sep="|"):
        "Recuperador de valores referenciales de c�digos de Tipos de Tributos"
        "Este m�todo permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposTributos(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret['FEParamGetTiposTributosResult']
        return [(u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p['TributoTipo']).replace("\t", sep)
                 for p in res['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ParamGetCotizacion(self, moneda_id):
        "Recuperador de cotizaci�n de moneda"
        ret = self.client.FEParamGetCotizacion(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            MonId=moneda_id,
            )
        self.__analizar_errores(ret)
        res = ret['FEParamGetCotizacionResult']['ResultGet']
        return str(res.get('MonCotiz',""))
        
    @inicializar_y_capturar_excepciones
    def ParamGetPtosVenta(self, sep="|"):
        "Recuperador de valores referenciales Puntos de Venta registrados"
        ret = self.client.FEParamGetPtosVenta(
            Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
            )
        res = ret.get('FEParamGetPtosVentaResult', {})
        return [(u"%(Nro)s\tEmisionTipo:%(EmisionTipo)s\tBloqueado:%(Bloqueado)s\tFchBaja:%(FchBaja)s" % p['PtoVenta']).replace("\t", sep)
                 for p in res.get('ResultGet', [])]

        
def p_assert_eq(a,b):
    print a, a==b and '==' or '!=', b

def main():
    "Funci�n principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    if DEBUG:
        from pysimplesoap.client import __version__ as soapver
        print "pysimplesoap.__version__ = ", soapver

    wsfev1 = WSFEv1()
    wsfev1.LanzarExcepciones = True

    cache = None
    wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
    proxy = ""
    wrapper = "" #"pycurl"
    cacert = None #geotrust.crt"

    ok = wsfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)
    
    if not ok:
        raise RuntimeError(wsfev1.Excepcion)

    if DEBUG:
        print "LOG: ", wsfev1.DebugLog()
        
    if "--dummy" in sys.argv:
        print wsfev1.client.help("FEDummy")
        wsfev1.Dummy()
        print "AppServerStatus", wsfev1.AppServerStatus
        print "DbServerStatus", wsfev1.DbServerStatus
        print "AuthServerStatus", wsfev1.AuthServerStatus
        sys.exit(0)


    # obteniendo el TA para pruebas
    from wsaa import WSAA
    ta = WSAA().Autenticar("wsfe", "reingart.crt", "reingart.key", debug=True)
    wsfev1.SetTicketAcceso(ta)
    wsfev1.Cuit = "20267565393"
    
    if "--prueba" in sys.argv:
        print wsfev1.client.help("FECAESolicitar").encode("latin1")

        tipo_cbte = 2 if '--usados' not in sys.argv else 49
        punto_vta = 4001
        cbte_nro = long(wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta) or 0)
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        concepto = 2 if '--usados' not in sys.argv else 1
        tipo_doc = 80 if '--usados' not in sys.argv else 30
        nro_doc = "30500010912" # CUIT BNA
        cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
        imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
        imp_iva = "21.00"; imp_trib = "1.00"; imp_op_ex = "0.00"
        fecha_cbte = fecha
        # Fechas del per�odo del servicio facturado y vencimiento de pago:
        if concepto > 1:
            fecha_venc_pago = fecha
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
        else:
            fecha_venc_pago = fecha_serv_desde = fecha_serv_hasta = None
        moneda_id = 'PES'; moneda_ctz = '1.000'

        wsfev1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz)
        
        # comprobantes asociados (notas de cr�dito / d�bito)
        if tipo_cbte in (1, 2, 3, 6, 7, 8, 11, 12, 13):
            tipo = 3
            pto_vta = 2
            nro = 1234
            wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro)
        
        # otros tributos:
        id = 99
        desc = 'Impuesto Municipal Matanza'
        base_imp = 100
        alic = 1
        importe = 1
        wsfev1.AgregarTributo(id, desc, base_imp, alic, importe)

        # subtotales por alicuota de IVA:
        id = 5 # 21%
        base_imp = 100
        importe = 21
        wsfev1.AgregarIva(id, base_imp, importe)

        # datos opcionales para proyectos promovidos:
        if '--proyectos' in sys.argv:
            wsfev1.AgregarOpcional(2, "1234")   # identificador del proyecto
        # datos opcionales para RG Bienes Usados 3411 (del vendedor):
        if '--usados' in sys.argv:
            wsfev1.AgregarOpcional(91, "Juan Perez")    # Nombre y Apellido 
            wsfev1.AgregarOpcional(92, "200")           # Nacionalidad
            wsfev1.AgregarOpcional(93, "Balcarce 50")   # Domicilio
        # datos opcionales para RG 3668 Impuesto al Valor Agregado - Art.12:
        if '--rg3668' in sys.argv:
            wsfev1.AgregarOpcional(5, "02")             # IVA Excepciones
            wsfev1.AgregarOpcional(61, "80")            # Firmante Doc Tipo
            wsfev1.AgregarOpcional(62, "20267565393")   # Firmante Doc Nro
            wsfev1.AgregarOpcional(7, "01")             # Car�cter del Firmante

        import time
        t0 = time.time()
        wsfev1.CAESolicitar()
        t1 = time.time()
        
        print "Resultado", wsfev1.Resultado
        print "Reproceso", wsfev1.Reproceso
        print "CAE", wsfev1.CAE
        print "Vencimiento", wsfev1.Vencimiento
        if DEBUG:
            print "t0", t0
            print "t1", t1
            print "lapso", t1-t0
            open("xmlrequest.xml","wb").write(wsfev1.XmlRequest)
            open("xmlresponse.xml","wb").write(wsfev1.XmlResponse)

        wsfev1.AnalizarXml("XmlResponse")
        p_assert_eq(wsfev1.ObtenerTagXml('CAE'), str(wsfev1.CAE))
        p_assert_eq(wsfev1.ObtenerTagXml('Concepto'), '2')
        p_assert_eq(wsfev1.ObtenerTagXml('Obs',0,'Code'), "10063")
        print wsfev1.ObtenerTagXml('Obs',0,'Msg')

        if "--reprocesar" in sys.argv:
            print "reprocesando...."
            wsfev1.Reproceso = True
            wsfev1.CAESolicitar()
    
    if "--get" in sys.argv:
        tipo_cbte = 2
        punto_vta = 4001
        cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)

        wsfev1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)

        print "FechaCbte = ", wsfev1.FechaCbte
        print "CbteNro = ", wsfev1.CbteNro
        print "PuntoVenta = ", wsfev1.PuntoVenta
        print "ImpTotal =", wsfev1.ImpTotal
        print "CAE = ", wsfev1.CAE
        print "Vencimiento = ", wsfev1.Vencimiento
        print "EmisionTipo = ", wsfev1.EmisionTipo
        
        wsfev1.AnalizarXml("XmlResponse")
        p_assert_eq(wsfev1.ObtenerTagXml('CodAutorizacion'), str(wsfev1.CAE))
        p_assert_eq(wsfev1.ObtenerTagXml('CbteFch'), wsfev1.FechaCbte)
        p_assert_eq(wsfev1.ObtenerTagXml('MonId'), "PES")
        p_assert_eq(wsfev1.ObtenerTagXml('MonCotiz'), "1")
        p_assert_eq(wsfev1.ObtenerTagXml('DocTipo'), "80")
        p_assert_eq(wsfev1.ObtenerTagXml('DocNro'), "30500010912")
            
    if "--parametros" in sys.argv:
        import codecs, locale, traceback
        if sys.stdout.encoding is None:
            sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
            sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

        print u'\n'.join(wsfev1.ParamGetTiposDoc())
        print "=== Tipos de Comprobante ==="
        print u'\n'.join(wsfev1.ParamGetTiposCbte())
        print "=== Tipos de Concepto ==="
        print u'\n'.join(wsfev1.ParamGetTiposConcepto())
        print "=== Tipos de Documento ==="
        print u'\n'.join(wsfev1.ParamGetTiposDoc())
        print "=== Alicuotas de IVA ==="
        print u'\n'.join(wsfev1.ParamGetTiposIva())
        print "=== Monedas ==="
        print u'\n'.join(wsfev1.ParamGetTiposMonedas())
        print "=== Tipos de datos opcionales ==="
        print u'\n'.join(wsfev1.ParamGetTiposOpcional())
        print "=== Tipos de Tributo ==="
        print u'\n'.join(wsfev1.ParamGetTiposTributos())
        print "=== Puntos de Venta ==="
        print u'\n'.join(wsfev1.ParamGetPtosVenta())

    if "--cotizacion" in sys.argv:
        print wsfev1.ParamGetCotizacion('DOL')

    if "--comptox" in sys.argv:
        print wsfev1.CompTotXRequest()
        
    if "--ptosventa" in sys.argv:
        print wsfev1.ParamGetPtosVenta()

    if "--solicitar-caea" in sys.argv:
        periodo = sys.argv[sys.argv.index("--solicitar-caea")+1]
        orden = sys.argv[sys.argv.index("--solicitar-caea")+2]

        if DEBUG: 
            print "Solicitando CAEA para periodo %s orden %s" % (periodo, orden)
        
        caea = wsfev1.CAEASolicitar(periodo, orden)
        print "CAEA:", caea

        if wsfev1.Errores:
            print "Errores:"
            for error in wsfev1.Errores:
                print error
            
        if DEBUG:
            print "periodo:", wsfev1.Periodo 
            print "orden:", wsfev1.Orden 
            print "fch_vig_desde:", wsfev1.FchVigDesde 
            print "fch_vig_hasta:", wsfev1.FchVigHasta 
            print "fch_tope_inf:", wsfev1.FchTopeInf 
            print "fch_proceso:", wsfev1.FchProceso

        if not caea:
            print 'Consultando CAEA'
            caea = wsfev1.CAEAConsultar(periodo, orden)
            print "CAEA:", caea
            if wsfev1.Errores:
                print "Errores:"
                for error in wsfev1.Errores:
                    print error

    if "--sinmovimiento-caea" in sys.argv:
        punto_vta = sys.argv[sys.argv.index("--sinmovimiento-caea")+1]
        caea = sys.argv[sys.argv.index("--sinmovimiento-caea")+2]

        if DEBUG: 
            print "Informando Punto Venta %s CAEA %s SIN MOVIMIENTO" % (punto_vta, caea)
        
        resultado = wsfev1.CAEASinMovimientoInformar(punto_vta, caea)
        print "Resultado:", resultado
        print "fch_proceso:", wsfev1.FchProceso

        if wsfev1.Errores:
            print "Errores:"
            for error in wsfev1.Errores:
                print error

                
# busco el directorio de instalaci�n (global para que no cambie si usan otra dll)
INSTALL_DIR = WSFEv1.InstallDir = get_install_dir()


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import pythoncom
        if TYPELIB: 
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "typelib", "wsfev1.tlb"))
                print "Registering %s" % (tlb,)
                tli=pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = WSFEv1
                pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                            k._typelib_version_[0], 
                                            k._typelib_version_[1], 
                                            0, 
                                            pythoncom.SYS_WIN32)
                print "Unregistered typelib"
        import win32com.server.register
        #print "_reg_class_spec_", WSFEv1._reg_class_spec_
        win32com.server.register.UseCommandLine(WSFEv1)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSFEv1._reg_clsid_])
    else:
        main()
