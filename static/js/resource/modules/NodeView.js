function NodeView() {
    var self = this;

    // Modules basic
    this.HTML 	                    = "";
    this.HostingID                  = "";
    this.DOMName                    = "";
    // Objects section
    this.HostingObject              = null;
    this.ComponentObject            = null;

    return this;
}

NodeView.prototype.SetObjectDOMName = function(name) {
    this.DOMName = name;
}

NodeView.prototype.SetHostingID = function(id) {
    this.HostingID = id;
}

NodeView.prototype.Build = function(data, callback) {
    var self = this;

    app.API.GetFileContent({
        "file_path": "modules/NodeView.html"
    }, function(res) {
        // Get payload
        var payload = res.payload;
        // Get HTML content
        self.HTML = app.API.ConvertHEXtoString(payload.content).replace("[ID]", self.HostingID);
        // Each UI module have encapsulated conent in component object (DIV)
        self.ComponentObject = document.getElementById("id_m_component_view_"+this.HostingID);
        // Apply HTML to DOM
        self.HostingObject = document.getElementById(self.HostingID);
        if (self.HostingObject !== undefined && self.HostingObject != null) {
            self.HostingObject.innerHTML = self.HTML;
        }

        // Call callback
        if (callback !== undefined && callback != null) {
            callback(self);
        }
    });
}

NodeView.prototype.Clean = function() {
}

NodeView.prototype.Hide = function() {
    var self = this;
    this.ComponentObject.classList.add("d-none")
}

NodeView.prototype.Show = function() {
    var self = this;
    this.ComponentObject.classList.remove("d-none")
}

NodeView.prototype.Back = function() {
    var self = this;
    console.log("Back");
    //this.Disconnect();
    window.ApplicationModules.DashboardView.Build(null, function(module) {});
}

NodeView.prototype.CallNode = function(hash, ip, port) {
    var self = this;
    console.log("CallNode");
    document.getElementById("id_m_nodeview_iframe").src = "http://"+ip+":"+port+"/?view=nested";
}
