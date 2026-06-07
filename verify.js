const express = require('express');
const router = express.Router();
const Project = require('../models/Project');
const Whitelist = require('../models/Whitelist');
const Key = require('../models/Key');
const Log = require('../models/Log');

// Main verification endpoint for Lua loader
router.post('/', async (req, res) => {
    const { key, hwid, projectName, version } = req.body;
    const clientIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

    try {
        // Find project
        const project = await Project.findOne({ name: projectName });
        if (!project) {
            return res.json({ status: 'error', message: 'Invalid project' });
        }

        // Find key
        const keyDoc = await Key.findOne({ code: key, projectId: project._id });
        if (!keyDoc) {
            await Log.create({ projectId: project._id, action: 'execution', details: { error: 'Invalid key' }, ip: clientIp });
            return res.json({ status: 'error', message: 'Invalid key' });
        }

        // Check if key is used
        if (!keyDoc.used) {
            return res.json({ status: 'error', message: 'Key not activated' });
        }

        // Check expiration
        if (keyDoc.duration !== 0 && new Date() > keyDoc.expiresAt) {
            return res.json({ status: 'error', message: 'Key expired' });
        }

        // Check whitelist
        const whitelistEntry = await Whitelist.findOne({ projectId: project._id, userId: keyDoc.usedBy });
        
        if (!whitelistEntry || whitelistEntry.isBlacklisted) {
            return res.json({ status: 'error', message: 'Not whitelisted or blacklisted' });
        }

        // Check HWID if lock enabled
        if (project.settings.hwidLock) {
            if (!whitelistEntry.hwid) {
                // First time HWID registration
                whitelistEntry.hwid = hwid;
                await whitelistEntry.save();
            } else if (whitelistEntry.hwid !== hwid) {
                await Log.create({ 
                    projectId: project._id, 
                    action: 'execution', 
                    userId: keyDoc.usedBy,
                    details: { error: 'HWID mismatch', expected: whitelistEntry.hwid, got: hwid },
                    ip: clientIp 
                });
                return res.json({ status: 'error', message: 'HWID mismatch' });
            }
        }

        // Log successful execution
        await Log.create({ 
            projectId: project._id, 
            action: 'execution', 
            userId: keyDoc.usedBy,
            userTag: keyDoc.usedByTag,
            details: { version, hwid },
            ip: clientIp 
        });

        // Calculate remaining days
        let remainingDays = null;
        if (keyDoc.duration !== 0) {
            remainingDays = Math.ceil((keyDoc.expiresAt - new Date()) / (1000 * 60 * 60 * 24));
        }

        res.json({
            status: 'success',
            message: 'Verified',
            data: {
                expiresAt: keyDoc.expiresAt,
                remainingDays,
                projectName: project.name,
                version: project.settings.scriptVersion,
                scriptUrl: project.settings.scriptUrl,
                user: {
                    discordId: keyDoc.usedBy,
                    tag: keyDoc.usedByTag
                }
            }
        });

    } catch (error) {
        console.error('Verification error:', error);
        res.json({ status: 'error', message: 'Internal error' });
    }
});

// HWID reset request from loader
router.post('/reset-hwid', async (req, res) => {
    const { key, hwid, projectName } = req.body;
    const clientIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

    try {
        const project = await Project.findOne({ name: projectName });
        if (!project) {
            return res.json({ status: 'error', message: 'Invalid project' });
        }

        const keyDoc = await Key.findOne({ code: key, projectId: project._id });
        if (!keyDoc || !keyDoc.used) {
            return res.json({ status: 'error', message: 'Invalid key' });
        }

        const whitelistEntry = await Whitelist.findOne({ projectId: project._id, userId: keyDoc.usedBy });
        
        if (!whitelistEntry) {
            return res.json({ status: 'error', message: 'Not whitelisted' });
        }

        // Check cooldown
        const cooldownDays = project.settings.hwidResetCooldown || 7;
        if (whitelistEntry.lastHwidReset) {
            const daysSinceReset = (new Date() - whitelistEntry.lastHwidReset) / (1000 * 60 * 60 * 24);
            if (daysSinceReset < cooldownDays) {
                return res.json({ 
                    status: 'error', 
                    message: `HWID reset on cooldown. Try again in ${Math.ceil(cooldownDays - daysSinceReset)} days` 
                });
            }
        }

        // Reset HWID
        whitelistEntry.hwid = hwid;
        whitelistEntry.lastHwidReset = new Date();
        whitelistEntry.hwidResetCount = (whitelistEntry.hwidResetCount || 0) + 1;
        await whitelistEntry.save();

        await Log.create({
            projectId: project._id,
            action: 'hwid_reset',
            userId: keyDoc.usedBy,
            details: { newHwid: hwid },
            ip: clientIp
        });

        res.json({ status: 'success', message: 'HWID reset successfully' });

    } catch (error) {
        console.error('HWID reset error:', error);
        res.json({ status: 'error', message: 'Internal error' });
    }
});

module.exports = router;
