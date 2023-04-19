

function sendJSON() {
    let jsonObj = {name: "Dan"} 
    xr = new XMLHttpRequest()
    xr.open("POST", "/test")
    xr.setRequestHeader("Content-Type", "application/json")

    xr.onreadystatechange = () => {
        if (xr.readyState == 4 && xr.status == 200) {
            console.log("Resp from server: " + xr.responseText)
        }
    }
    xr.send(JSON.stringify(jsonObj))
}


//main
sendJSON()
