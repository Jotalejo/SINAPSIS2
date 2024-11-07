/* Enciende un campo para capturar datos, el textAreaaP es el nombre del select, el otro la variable que la activa  */
function PrendaDt(textAreaaP, opci) {
    tagdSel = "#" + opci;
    eldato = document.querySelector(tagdSel).value
    if (eldato=="Otros") {
        tagdTA = "#" + textAreaaP;
        document.querySelector(tagdTA).style.display = 'block';        
    }
    else
        document.querySelector(tagdTA).style.display = 'none';
    return false;
}

/* Enciende un campo para capturar datos, el textAreaaP es el nombre del select, el otro la variable que la activa  
    También activa el botón de grabación para el formulario
*/
function PrendaDtyG(textAreaaP, opci, elBtgr) {
    tagdBtnG = "#" + elBtgr;
    document.querySelector(tagdBtnG).style.display = 'block';
    
    tagdSel = "#" + opci;
    eldato = document.querySelector(tagdSel).value
    if (eldato=="Otros") {
        tagdTA = "#" + textAreaaP;
        document.querySelector(tagdTA).style.display = 'block';        
    }
    else
        document.querySelector(tagdTA).style.display = 'none';

    alert("sitinos");
    hacElcod();
    
    return false;
}


/* La Fecha de hoy y le suma unos días para entregas posteriores si se quiere */
function lefechoy(tagadondeva, diasae) {

    var fecha = new Date(); //Fecha actual más los días
    var dia = fecha.getDate(); //obteniendo dia
    fecha.setDate(dia+diasae);
    var dia = fecha.getDate(); //obteniendo dia nuevamente
    var mes = fecha.getMonth()+1; //obteniendo mes
    var ano = fecha.getFullYear(); //obteniendo año

    d1=String(dia).length;
    if (d1 == 1 ) {
        dia = "0"+dia;
    }

    d1=String(mes).length;
    if (d1 == 1 ) {
        mes = "0"+mes;
    }

    var pruebaf = (ano+"-"+mes+"-"+dia);

    var verav = document.querySelector(tagadondeva).value;
    if (verav == '' ) {
        document.querySelector(tagadondeva).value=pruebaf;
        //document.querySelector(tagadondeva).style.fontSize = "12.5px";
    }
    return false;
}

/* La Hora actual para actualizar un campo */
function lahrhoy(tagahora) {   
    var fecha = new Date(); //Fecha actual y hora
    var horaj = fecha.getHours(); //obteniendo hora actual
    var minuj = fecha.getMinutes(); //obteniendo hora actual
    var loraco = horaj+":"+minuj;
    document.querySelector(tagahora).value = loraco;
    return false;
}

/* Desbloque los campos para poder grabar */	
function GrabacS() {
    cdfechsoli = "#" + fechsoli;
    document.querySelector(cdfechsoli).disabled=false

    cdahradsolicit = "#" + hradsolicit;
    document.querySelector(cdahradsolicit).disabled=false

    cdanradic = "#" + nradic;
    document.querySelector(cdanradic).disabled=false

    return false;
}

/* Generar el código del No. Radicado */
function hacElcod() {

    "{% for codsolici in maxcodsol %}"
        var mxcosol = "{{ codsolici.1 }}";
    "{% endfor %}"

    return false;
}

