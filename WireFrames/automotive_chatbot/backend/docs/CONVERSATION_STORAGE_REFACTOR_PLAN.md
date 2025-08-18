# Conversation Storage Refactor Plan

## 概述
本文档详细说明如何重构会话存储系统，同时完全保留现有的客户端配置功能。

## 当前客户端配置系统分析

### 前端配置 (test-client-widget.html)
```javascript
// 第72行：设置客户端ID
window.CleverCompanionConfig = { clientId: '689c9761bc4138c381b17f66' };

// 第74-90行：动态加载widget脚本
// 自动检测环境并加载相应的widget文件
```

### 后端配置API
- **端点**: `/api/config/{client_id}`
- **功能**: 返回客户端配置信息
- **数据**: 包含电话、邮箱、营业时间、品牌设置等

### Widget配置流程
1. `test-client-widget.html` 设置 `clientId`
2. `clevercompanion-widget.js` 调用 `getClientConfigFromDB()`
3. 后端 `/api/config/{client_id}` 返回客户端配置
4. Widget根据配置显示相应信息

## 重构策略：保持客户端配置不变

### 原则
1. **零修改原则**: 不修改 `test-client-widget.html` 中的任何代码
2. **向后兼容**: 保持所有现有API端点完全不变
3. **渐进式重构**: 新增统一服务，逐步迁移功能
4. **数据一致性**: 确保客户端信息提取功能正常

### 重构步骤

#### 第一阶段：创建统一服务层

1. **创建统一Session管理器**
   ```
   backend/api/services/unified_session_manager.py
   ```
   - 统一前后端session管理逻辑
   - 处理session过期和续期
   - 生成唯一conversation_id

2. **创建统一Conversation服务**
   ```
   backend/api/services/conversation_service.py
   ```
   - 统一会话存储逻辑
   - 处理消息存储和检索
   - 管理会话历史

3. **保持现有API端点**
   - `/api/config/{client_id}` - **完全不变**
   - `/api/conversations/store` - **保持兼容**
   - `/api/widget/conversations/store` - **保持兼容**

#### 第二阶段：添加新的统一API

1. **新增统一端点**
   ```
   /api/v2/sessions/create
   /api/v2/sessions/{session_id}/messages
   /api/v2/sessions/{session_id}/history
   ```

2. **向后兼容层**
   - 现有端点调用新的统一服务
   - 保持响应格式不变
   - 确保客户端配置功能正常

#### 第三阶段：优化和测试

1. **数据迁移**
   - 确保现有会话数据完整性
   - 验证客户端配置数据

2. **功能测试**
   - 测试客户端信息提取
   - 验证会话存储功能
   - 确保widget正常工作

## 客户端配置保护措施

### 1. API端点保护
```python
# main.py - 保持不变
@app.get("/api/config/{client_id}")
async def get_client_config(client_id: str):
    # 此端点完全不修改
    # 确保客户端信息提取功能正常
```

### 2. Widget兼容性
```javascript
// clevercompanion-widget.js - 保持现有功能
// getClientConfigFromDB() 方法保持不变
// 客户端信息提取逻辑保持不变
```

### 3. 数据库结构
```python
# client.py - 保持现有模型
class ClientSettings(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    business_hours: Optional[Dict] = None
    # 所有现有字段保持不变
```

## 重构实施计划

### 阶段1：基础服务创建 (1-2天)
- [ ] 创建 `unified_session_manager.py`
- [ ] 创建 `conversation_service.py`
- [ ] 添加新的API端点
- [ ] 确保所有现有端点正常工作

### 阶段2：兼容性测试 (1天)
- [ ] 测试客户端配置API
- [ ] 验证widget加载和配置
- [ ] 确认客户端信息显示正常

### 阶段3：会话存储优化 (1-2天)
- [ ] 统一会话管理逻辑
- [ ] 优化数据存储结构
- [ ] 测试完整功能

## 风险控制

### 1. 零影响保证
- 客户端配置代码完全不修改
- 现有API端点保持100%兼容
- Widget功能保持完全正常

### 2. 回滚策略
- 新服务独立部署
- 可随时切换回原有逻辑
- 数据备份和恢复机制

### 3. 测试覆盖
- 客户端信息提取测试
- Widget加载和配置测试
- 端到端功能测试

## 总结

通过这个重构计划，我们可以：
1. **完全保留** `test-client-widget.html` 中的客户端配置代码
2. **确保** 客户端信息提取功能正常工作
3. **解决** 会话存储的冲突和重复问题
4. **提供** 更好的系统架构和维护性

重构过程中，客户端配置功能将完全不受影响，用户可以继续正常使用所有现有功能。