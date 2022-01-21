function DasboardView() {
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

DasboardView.prototype.SetObjectDOMName = function(name) {
    this.DOMName = name;
}

DasboardView.prototype.SetHostingID = function(id) {
    this.HostingID = id;
}

DasboardView.prototype.Build = function(data, callback) {
    var self = this;

    app.API.GetFileContent({
        "file_path": "modules/DasboardView.html"
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

        self.UpdateNodes();

        // Call callback
        if (callback !== undefined && callback != null) {
            callback(self);
        }
    });
}

DasboardView.prototype.Clean = function() {
}

DasboardView.prototype.Hide = function() {
    var self = this;
    this.ComponentObject.classList.add("d-none")
}

DasboardView.prototype.Show = function() {
    var self = this;
    this.ComponentObject.classList.remove("d-none")
}

DasboardView.prototype.UpdateNodes = function() {
    var self = this;

    app.Adaptor.GetNodes(function(data, error) {
        console.log(data);
        var MAX_COLUMNS = 6;
        var nodesCount = Object.keys(data.payload.users).length;
        var rowsCount = (parseInt(nodesCount / MAX_COLUMNS)) + 1;
        var leftoverColumn = nodesCount % MAX_COLUMNS;

        var html = ``;
        if (nodesCount > 0) {
            html = `<div class="row">`;
            var index = 1;
            for (key in data.payload.users) {
                var node = data.payload.users[key];
                console.log(node);
                if (index % MAX_COLUMNS == 0) {
                    html += `</div><div class="row">`;
                }
                var column = `
                    <div class="col-xl-2" style="text-align: center;" id="id_m_dashboardview_node_`+node.data.hash+`">
                        <div class="card-deck mb-3 text-center">
                            <div class="card mb-4 shadow-sm">
                                <div class="card-header">
                                    <h6 class="my-0 font-weight-normal">`+node.data.name+`</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled mt-3 mb-4">
                                        <li>Description</li>
                                    </ul>
                                    <button type="button" class="btn btn-sm btn-block btn-outline-primary" onclick="window.ApplicationModules.DashboardView.LoadNode('`+node.data.hash+`','`+node.sender.ip+`',`+node.data.server.web.port+`);">Launch</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                html += column;
            }
            html += `</div>`;
            /*
            for (rowidx = 0; rowidx < rowsCount; rowidx++) {
                var coeff = rowsCount / (rowidx + 1);
                console.log(coeff);
                html = `<div class="row">`;
                for (i = 0; i < (MAX_COLUMNS - MAX_COLUMNS * coeff) + (leftoverColumn * coeff); i++) {
                    node = data.payload.users[i + rowidx * rowsCount];
                    console.log(rowidx, i);
                }
                html += `</div>`;
            }
            */
        }

        document.getElementById("m_dashboardview_nodes_table").innerHTML = html;
    })
}

DasboardView.prototype.LoadNode = function(hash, ip, port) {
    var self = this;
    console.log(hash, ip, port);
    window.ApplicationModules.NodeView.Build(null, function(module) {
        module.CallNode(hash, ip, port);
    });
}
