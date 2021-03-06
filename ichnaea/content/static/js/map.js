$(document).ready(function() {
    // the retina version uses zoom level + 1 image tiles
    // and we only generated tiles down to zoom level 13
    var maxZoom = 13;
    if (L.Browser.retina) {
        maxZoom = 12;
    }

    var map = L.mapbox.map('map', 'mozilla-webprod.map-05ad0a21', {
        minZoom: 1,
        maxZoom: maxZoom,
        tileLayer: { detectRetina: true }
    }).setView([15.0, 10.0], 2);

    var hash = new L.Hash(map);

    // add open street map attribution for base tiles
    map.infoControl.addInfo(
        '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    );

    // add scale
    L.control.scale({
        'updateWhenIdle': true,
        'imperial': false,
        'maxWidth': 200
    }).addTo(map);

    // add tile layer
    L.tileLayer('/tiles/{z}/{x}/{y}.png', {
        detectRetina: true
    }).addTo(map);

    // add tile layer
    L.mapbox.tileLayer('mozilla-webprod.map-5e1cee8a', {
        detectRetina: true
    }).addTo(map);

});
