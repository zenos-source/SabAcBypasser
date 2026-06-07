const mongoose = require('mongoose');

const whitelistSchema = new mongoose.Schema({
    projectId: { type: mongoose.Schema.Types.ObjectId, ref: 'Project', required: true },
    userId: { type: String, required: true },
    userTag: { type: String },
    expiresAt: { type: Date, required: true },
    hwid: { type: String },
    keyId: { type: mongoose.Schema.Types.ObjectId, ref: 'Key' },
    isBlacklisted: { type: Boolean, default: false },
    blacklistReason: { type: String },
    blacklistedAt: { type: Date },
    createdAt: { type: Date, default: Date.now }
});

whitelistSchema.index({ projectId: 1, userId: 1 }, { unique: true });

module.exports = mongoose.model('Whitelist', whitelistSchema);
