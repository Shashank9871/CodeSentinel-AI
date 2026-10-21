"""
Realistic sample Pull Requests and Code Diffs for instant demonstration.
"""

SAMPLES = [
    {
        "id": "sample-auth-vuln",
        "title": "PR #104: Add User Authentication & Backup Service",
        "author": "dev-alex",
        "branch": "feature/auth-and-backup -> main",
        "language": "python",
        "description": "Implements user password authentication, session token generation, and an automated database backup utility.",
        "code": '''import os
import hashlib
import sqlite3
import subprocess

# Sensitive configuration
SECRET_KEY = "super_secret_jwt_signing_key_12345"
AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE_SECRET_TOKEN"

def authenticate_user(username, raw_password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # MD5 password hashing
    hashed_pw = hashlib.md5(raw_password.encode()).hexdigest()
    
    # Vulnerable to SQL injection
    query = f"SELECT id, role FROM users WHERE username = '{username}' AND password = '{hashed_pw}'"
    print(f"Executing authentication query: {query}")
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    return user

def trigger_database_backup(db_name, destination_folder):
    # Potential Remote Code Execution via shell=True
    cmd = f"cp {db_name} {destination_folder}"
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception:
        pass  # Silently suppress any backup errors
    return True
'''
    },
    {
        "id": "sample-node-payment",
        "title": "PR #215: Wallet Balance Debit & Payment Webhook",
        "author": "backend-sam",
        "branch": "fix/payment-race -> staging",
        "language": "javascript",
        "description": "Handles wallet debit operations, logs transaction history in memory, and accepts incoming payment webhooks.",
        "code": '''const express = require('express');
const router = express.Router();

// Memory leak: Unbounded global array storing every request body
const transactionAuditHistory = [];

router.post('/debit', async (req, res) => {
    const { userId, amount } = req.body;
    
    // In-memory audit history keeps growing without eviction
    transactionAuditHistory.push(req.body);

    const user = await db.getUser(userId);
    
    // Race condition: Non-atomic read-then-write
    if (user.balance >= amount) {
        user.balance = user.balance - amount;
        await db.saveUser(user);
        console.log("Processed debit for user: " + userId + " amount: " + amount);
        return res.json({ success: true, balance: user.balance });
    } else {
        return res.status(400).json({ error: "Insufficient funds" });
    }
});

router.post('/webhook', (req, res) => {
    try {
        // Dangerous dynamic code execution on incoming webhook payload
        const handler = eval(req.body.customScript);
        handler();
        res.sendStatus(200);
    } catch (err) {
        // Swallowed error
    }
});

module.exports = router;
'''
    },
    {
        "id": "sample-react-leak",
        "title": "PR #88: Real-Time Stock Ticker Component",
        "author": "frontend-maya",
        "branch": "feature/stock-ticker -> main",
        "language": "javascript",
        "description": "Adds a real-time polling widget displaying latest stock prices and renders live updates.",
        "code": '''import React, { useState, useEffect } from 'react';

export function StockTicker({ symbol }) {
    const [price, setPrice] = useState(0);
    const [rawFeed, setRawFeed] = useState("<span style='color:green'>Live</span>");

    useEffect(() => {
        // Memory leak: missing cleanup function for setInterval
        const interval = setInterval(() => {
            fetch(`/api/stocks/${symbol}`)
                .then(res => res.json())
                .then(data => setPrice(data.price));
        }, 1000);
    }); // Missing dependency array triggers re-subscription on every render!

    return (
        <div className="ticker-card">
            <h3>{symbol}</h3>
            <p>Current: ${price}</p>
            {/* Cross-site scripting risk */}
            <div dangerouslySetInnerHTML={{ __html: rawFeed }} />
        </div>
    );
}
'''
    },
    {
        "id": "sample-clean-go",
        "title": "PR #340: Optimized Cache Manager with LRU Eviction",
        "author": "systems-sarah",
        "branch": "feature/lru-cache -> main",
        "language": "go",
        "description": "Thread-safe LRU cache implementation with RWMutex and automated expiration policy.",
        "code": '''package cache

import (
	"sync"
	"time"
)

type CacheItem struct {
	Value      interface{}
	Expiration int64
}

type LRUCache struct {
	mu    sync.RWMutex
	items map[string]CacheItem
}

func NewLRUCache() *LRUCache {
	return &LRUCache{
		items: make(map[string]CacheItem),
	}
}

func (c *LRUCache) Set(key string, value interface{}, duration time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	c.items[key] = CacheItem{
		Value:      value,
		Expiration: time.Now().Add(duration).UnixNano(),
	}
}

func (c *LRUCache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	item, found := c.items[key]
	if !found {
		return nil, false
	}
	if time.Now().UnixNano() > item.Expiration {
		return nil, false
	}
	return item.Value, true
}
'''
    }
]

def get_sample_by_id(sample_id: str):
    for s in SAMPLES:
        if s["id"] == sample_id:
            return s
    return None
