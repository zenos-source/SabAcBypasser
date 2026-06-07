const mongoose = require('mongoose');

const projectSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    ownerId: { type: String, required: true },
    ownerDiscordTag: { type: String },
    description: { type: String },
    settings: {
        hwidLock: { type: Boolean, default: true },
        hwidResetCooldown: { type: Number, default: 7 }, // days
        buyerRoleId: { type: String },
        redeemChannelId: { type: String },
        logWebhook: { type: String },
        scriptUrl: { type: String },
        scriptVersion: { type: String, default: "1.0.0" }
    },
    createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Project', projectSchema);
