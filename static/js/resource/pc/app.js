function Application() {
    var self = this;
    // Get makesense api instanse.
    this.API = MkSAPIBuilder.GetInstance();
    // Default handler
    this.API.OnUnexpectedDataArrived = function (packet) {
        console.log(packet);
    }
    this.API.ModulesLoadedCallback = function () {
        self.NodeLoaded();
    }
    this.EventMapper = {};
    this.Adaptor = new Pidaptor(this.API);
    this.Terminal = new Piterm(this.API);
    window.ApplicationModules.Modal = new MksBasicModal("GLOBAL");

    return this;
}
Application.prototype.RegisterEventHandler = function(name, callback, scope) {
    this.EventMapper[name] = { 
        callback: callback,
        scope: scope
    };
}
Application.prototype.UnregisterEventHandler = function(name) {
    delete this.EventMapper[name];
}
Application.prototype.Publish = function(name, data) {
    var handler  = this.EventMapper[name];
    if (handler !== undefined && handler !== null) {
        handler.callback(data, handler.scope);
    }
}
Application.prototype.Connect = function(ip, port, callback) {
    var self = this;
    console.log("Connect Application");
    // Python will emit messages
    self.API.OnNodeChangeCallback = self.OnChangeEvent.bind(self);
    this.API.ConnectLocalWS(ip, port, function() {
        console.log("Connected to local websocket");

        // Module area
        self.API.AppendModule("DasboardView");
        self.API.AppendModule("NodeView");
        self.API.GetModules();

        callback();
    });
}
Application.prototype.NodeLoaded = function () {
    console.log("Modules Loaded");
    window.ApplicationModules.DashboardView = new DasboardView();
    window.ApplicationModules.DashboardView.SetHostingID("id_application_view_module");
    window.ApplicationModules.DashboardView.SetObjectDOMName("window.ApplicationModules.DasboardView");
    window.ApplicationModules.DashboardView.Build(null, function(module) {});

    window.ApplicationModules.NodeView = new NodeView();
    window.ApplicationModules.NodeView.SetHostingID("id_application_view_module");
    window.ApplicationModules.NodeView.SetObjectDOMName("window.ApplicationModules.NodeView");
}
Application.prototype.OnChangeEvent = function(packet) {
    var event = packet.payload.event;
    var data = packet.payload.data;
    this.Publish(event, data);
}
// ASYNC REGISTERED HANDLERS
Application.prototype.UndefinedHandler = function(data, scope) {
    console.log(data);
}
Application.prototype.NodesHandler = function(data, scope) {
    console.log(data);
    window.ApplicationModules.DashboardView.UpdateNodes()
}

var app = new Application();

app.RegisterEventHandler("undefined", app.UndefinedHandler, app);
app.RegisterEventHandler("nodes", app.NodesHandler, app);
app.Connect(global_ip, global_port, function() {});

feather.replace();