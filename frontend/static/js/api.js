// API Client Module
const API = {
    baseURL: window.location.origin,

    async getStatus() {
        const res = await fetch(`${this.baseURL}/api/status`);
        return res.json();
    },

    async getDevices() {
        const res = await fetch(`${this.baseURL}/api/devices`);
        return res.json();
    },

    async addDevice(deviceId, enabled) {
        const res = await fetch(`${this.baseURL}/api/devices/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, enabled })
        });
        return res.json();
    },

    async removeDevice(deviceId) {
        const res = await fetch(`${this.baseURL}/api/devices/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, enabled: false })
        });
        return res.json();
    },

    async toggleDevice(deviceId, enabled) {
        const res = await fetch(`${this.baseURL}/api/devices/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, enabled })
        });
        return res.json();
    },

    async getDeviceKeys(deviceId) {
        const res = await fetch(`${this.baseURL}/api/devices/${deviceId}/keys`);
        return res.json();
    },

    async getMappings(deviceId) {
        const res = await fetch(`${this.baseURL}/api/mappings/${deviceId}`);
        return res.json();
    },

    async updateMappings(deviceId, mappings) {
        const res = await fetch(`${this.baseURL}/api/mappings/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, mappings })
        });
        return res.json();
    },

    async updateIgnoredKeys(deviceId, ignoredKeys) {
        const res = await fetch(`${this.baseURL}/api/mappings/ignored`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, ignored_keys: ignoredKeys })
        });
        return res.json();
    },

    async getMQTTConfig() {
        const res = await fetch(`${this.baseURL}/api/mqtt/config`);
        return res.json();
    },

    async updateMQTTConfig(config) {
        const res = await fetch(`${this.baseURL}/api/mqtt/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return res.json();
    },

    async testMQTT() {
        const res = await fetch(`${this.baseURL}/api/mqtt/test`, { method: 'POST' });
        return res.json();
    },

    async getMasterStatus() {
        const res = await fetch(`${this.baseURL}/api/master`);
        return res.json();
    },

    async toggleMaster(enabled) {
        const res = await fetch(`${this.baseURL}/api/master/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
        return res.json();
    },

    async getBluetoothDevices(scan = false) {
        const res = await fetch(`${this.baseURL}/api/bluetooth/devices?scan=${scan}`);
        return res.json();
    },

    async scanBluetooth() {
        const res = await fetch(`${this.baseURL}/api/bluetooth/scan`, { method: 'POST' });
        return res.json();
    },

    async bluetoothCommand(address, action, value = null) {
        const res = await fetch(`${this.baseURL}/api/bluetooth/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, action, value })
        });
        return res.json();
    },

    async getLogs(limit = 100, level = null) {
        let url = `${this.baseURL}/api/logs?limit=${limit}`;
        if (level) url += `&level=${level}`;
        const res = await fetch(url);
        return res.json();
    },

    async clearLogs() {
        const res = await fetch(`${this.baseURL}/api/logs/clear`, { method: 'POST' });
        return res.json();
    },

    async exportConfig() {
        const res = await fetch(`${this.baseURL}/api/config/export`);
        return res.json();
    },

    async importConfig(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${this.baseURL}/api/config/import`, {
            method: 'POST',
            body: formData
        });
        return res.json();
    }
};
