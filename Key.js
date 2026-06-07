const mongoose = require('mongoose');

const keySchema = new mongoose.Schema({
    code: { type: String, required: true, unique: true },
    projectId: { type: mongoose.Schema.Types.ObjectId, ref: 'Project', required: true },
    duration: { type: Number, required: true }, // days, 0 = lifetime
    used: { type: Boolean, default: false },
    usedBy: { type: String }, // discord user id
    usedByTag: { type: String },
    redeemedAt: { type: Date },
    expiresAt: { type: Date },
    hwid: { type: String },
    hwidResetCount: { type: Number, default: 0 },
    lastHwidReset: { type: Date },
    notes: { type: String },
    createdAt: { type: Date, default: Date.now },
    createdBy: { type: String }
});

module.exports = mongoose.model('Key', keySchema);
