const mongoose = require('mongoose');

const logSchema = new mongoose.Schema({
    projectId: { type: mongoose.Schema.Types.ObjectId, ref: 'Project' },
    action: { type: String, enum: ['key_redeem', 'hwid_reset', 'execution', 'whitelist_add', 'whitelist_remove', 'blacklist'] },
    userId: { type: String },
    userTag: { type: String },
    details: { type: Object },
    ip: { type: String },
    timestamp: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Log', logSchema);
