function showDetail(id, start, cil, hrana) {
  console.log(id)
  if (document.getElementById("detail"+id).innerHTML === "") {  
      if ((id === "") || (start === "") || (cil === "") || (hrana === "")) {
        document.getElementById("detail"+id).innerHTML = "";
        return;
      } else {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function() {
          if (this.readyState == 4 && this.status == 200) {
            document.getElementById("detail"+id).innerHTML = this.responseText;
          }
        };
        xmlhttp.open("GET","detail/"+start+"/"+cil+"/"+hrana,true);
        xmlhttp.send();
      }
  } else {
      document.getElementById("detail"+id).innerHTML = "";
      document.getElementById("btn"+id).blur();
  }    
}

function showRoute(id) {
  if (document.getElementById("route"+id).innerHTML === "") {  
      if (id === "") {
        document.getElementById("route"+id).innerHTML = "";
        return;
      } else {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function() {
          if (this.readyState == 4 && this.status == 200) {
            document.getElementById("route"+id).innerHTML = this.responseText;
          }
        };
        xmlhttp.open("GET","detail_trasy/"+id,true);
        xmlhttp.send();
      }
  } else {
      document.getElementById("route"+id).innerHTML = "";
      document.getElementById("btn"+id).blur();
  }    
}

function setCookie(cname, cvalue, exdays) {
  var d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  var expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

        function getDocHeight() {
            var D = document;
            return Math.max(
            D.body.scrollHeight, D.documentElement.scrollHeight,
            D.body.offsetHeight, D.documentElement.offsetHeight,
            D.body.clientHeight, D.documentElement.clientHeight
            );
        }
        
        function isMobile() {
            try{ document.createEvent("TouchEvent"); return true; }
            catch(e){ return false; }
        }
        
        function saveCookies(form2) {
           var i;
           var starts;
           var element;
           for (i = 3000; i < 3297; i++) {
                 element = document.getElementById("start"+i);
                 if (element) {starts += element.selected + ",";}
           }
           setCookie("starts", starts, 30); 
           var cils;
           for (i = 3000; i < 3297; i++) {
                 element = document.getElementById("cil"+i);
                 if (element) {cils += element.selected + ",";}
           }
           setCookie("cils", cils, 30);            
           setCookie("Praha", form2.Praha.checked, 30);
           setCookie("razeni", form2.razeni.value, 30);
           return true;
        }
        
        function loadCookies(form2) {
           chbchecked = (getCookie("Praha") == "true");
           form2.Praha.checked = chbchecked;
           var i;
           var starts = getCookie("starts");
           var arr = starts.split(",");
           for (i = 3000; i < 3297; i++) {
             var element = document.getElementById("start"+i);
             if (element) 
               {element.selected = (arr.includes(i));}
           }       
           var cils = getCookie("cils");
           arr = cils.split(",");
           for (i = 3000; i < 3297; i++) {
             var element = document.getElementById("cil"+i);
             if (element) 
               {element.selected = (arr.includes(i));}                
           }   
           form2.razeni.value = getCookie("razeni");
           return true;
        }
        
        function setFilterCombos() {
//            $('#start').find('option').first().remove();
  //          $('#cil').find('option').first().remove();
            return true;
        }

