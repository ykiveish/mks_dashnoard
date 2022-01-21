function Pidaptor(api) {
    var self = this;
    this.API = api;

    return this;
}
Pidaptor.prototype.Echo = function(sensor_id, callback) {
    this.API.SendCustomCommand("echo", {
        "async": false
    }, function(data, error) {
        callback(data, error);
    });
}
Pidaptor.prototype.GetNodes = function(callback) {
    this.API.SendCustomCommand("nodes", {
        "async": false
    }, function(data, error) {
        callback(data, error);
    });
}