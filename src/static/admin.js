let adminPassword = '';

function login() {
    const password = document.getElementById('password').value;
    
    if (!password) {
        showError('请输入密码');
        return;
    }
    
    adminPassword = password;
    
    fetch('/admin/api/statistics', {
        method: 'POST',
        headers: {
            'X-Admin-Password': password
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            document.getElementById('loginContainer').style.display = 'none';
            document.getElementById('mainContainer').style.display = 'flex';
            loadDashboard();
            loadApps();
            loadVersions();
            loadReviews();
            loadUsers();
        } else {
            showError('密码错误');
        }
    })
    .catch(() => {
        showError('登录失败，请检查网络');
    });
}

function logout() {
    adminPassword = '';
    document.getElementById('loginContainer').style.display = 'flex';
    document.getElementById('mainContainer').style.display = 'none';
    document.getElementById('password').value = '';
}

function showError(message) {
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = message;
    setTimeout(() => {
        errorEl.textContent = '';
    }, 3000);
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.nav-btn[data-tab="${tabName}"]`).classList.add('active');
    
    const titles = {
        dashboard: '仪表盘',
        apps: '应用管理',
        versions: '版本审核',
        reviews: '评论管理',
        users: '用户管理'
    };
    document.getElementById('pageTitle').textContent = titles[tabName];
    
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'apps') loadApps();
    if (tabName === 'versions') loadVersions();
    if (tabName === 'reviews') loadReviews();
    if (tabName === 'users') loadUsers();
}

function loadDashboard() {
    fetch('/admin/api/statistics', {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            const stats = data.data;
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <h3>应用总数</h3>
                    <div class="stat-number">${stats.apps.total}</div>
                    <small>待审核: ${stats.apps.pending}</small>
                </div>
                <div class="stat-card">
                    <h3>版本总数</h3>
                    <div class="stat-number">${stats.versions.total}</div>
                    <small>待审核: ${stats.versions.pending}</small>
                </div>
                <div class="stat-card">
                    <h3>评论总数</h3>
                    <div class="stat-number">${stats.reviews.total}</div>
                </div>
                <div class="stat-card">
                    <h3>用户总数</h3>
                    <div class="stat-number">${stats.users.total}</div>
                    <small>7日新增: ${stats.users.new_last_7_days}</small>
                </div>
                <div class="stat-card">
                    <h3>总下载量</h3>
                    <div class="stat-number">${stats.downloads.total}</div>
                    <small>7日下载: ${stats.downloads.last_7_days}</small>
                </div>
            `;
        }
    });
}

function loadApps() {
    const status = document.getElementById('appStatusFilter').value;
    
    fetch(`/admin/api/apps?skip=0&limit=100&status=${status}`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            const apps = data.data;
            const appsList = document.getElementById('appsList');
            
            if (apps.length === 0) {
                appsList.innerHTML = '<p style="padding: 40px; text-align: center; color: #64748b;">暂无数据</p>';
                return;
            }
            
            let html = '<table><thead><tr>';
            html += '<th>ID</th><th>名称</th><th>分类</th><th>开发者</th><th>状态</th><th>下载量</th><th>评分</th><th>版本数</th><th>创建时间</th><th>操作</th>';
            html += '</tr></thead><tbody>';
            
            apps.forEach(app => {
                let statusClass = '';
                if (app.status === 'pending') statusClass = 'status-pending';
                else if (app.status === 'approved') statusClass = 'status-approved';
                else if (app.status === 'rejected') statusClass = 'status-rejected';
                else statusClass = 'status-removed';
                
                let statusText = '';
                if (app.status === 'pending') statusText = '待审核';
                else if (app.status === 'approved') statusText = '已通过';
                else if (app.status === 'rejected') statusText = '已拒绝';
                else statusText = '已下架';
                
                html += `<tr>
                    <td>${app.id}</td>
                    <td>${escapeHtml(app.name)}</td>
                    <td>${app.category}</td>
                    <td>${escapeHtml(app.developer_name)}</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td>${app.total_downloads}</td>
                    <td>${app.average_rating.toFixed(1)}</td>
                    <td>${app.versions_count}</td>
                    <td>${new Date(app.created_at).toLocaleDateString()}</td>
                    <td class="action-btns">`;
                
                if (app.status === 'pending') {
                    html += `<button class="action-btn action-approve" onclick="approveApp(${app.id})">通过</button>`;
                    html += `<button class="action-btn action-reject" onclick="rejectApp(${app.id})">拒绝</button>`;
                }
                
                if (app.status === 'approved') {
                    html += `<button class="action-btn action-reject" onclick="removeApp(${app.id})">下架</button>`;
                }
                
                html += `</td></tr>`;
            });
            
            html += '</tbody></table>';
            appsList.innerHTML = html;
        }
    });
}

function approveApp(appId) {
    if (!confirm('确定要通过这个应用吗？')) return;
    
    fetch(`/admin/api/apps/${appId}/approve`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('应用已通过审核');
            loadApps();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function rejectApp(appId) {
    const reason = prompt('请输入拒绝原因（可选）：');
    
    const formData = new FormData();
    if (reason) formData.append('reason', reason);
    
    fetch(`/admin/api/apps/${appId}/reject`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('应用已拒绝');
            loadApps();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function removeApp(appId) {
    if (!confirm('确定要下架这个应用吗？')) return;
    
    fetch(`/admin/api/apps/${appId}/remove`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('应用已下架');
            loadApps();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function loadVersions() {
    fetch('/admin/api/versions/pending?skip=0&limit=100', {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            const versions = data.data;
            const versionsList = document.getElementById('versionsList');
            
            if (versions.length === 0) {
                versionsList.innerHTML = '<p style="padding: 40px; text-align: center; color: #64748b;">暂无待审核版本</p>';
                return;
            }
            
            let html = '<table><thead><tr>';
            html += '<th>ID</th><th>应用名称</th><th>版本号</th><th>版本代码</th><th>文件大小</th><th>开发者</th><th>更新日志</th><th>创建时间</th><th>操作</th>';
            html += '</tr></thead><tbody>';
            
            versions.forEach(version => {
                html += `<tr>
                    <td>${version.id}</td>
                    <td>${escapeHtml(version.app_name)}</td>
                    <td>${version.version}</td>
                    <td>${version.version_code}</td>
                    <td>${version.file_size}</td>
                    <td>${escapeHtml(version.developer_name)}</td>
                    <td>${escapeHtml(version.release_notes || '').substring(0, 50)}</td>
                    <td>${new Date(version.created_at).toLocaleDateString()}</td>
                    <td class="action-btns">
                        <button class="action-btn action-approve" onclick="approveVersion(${version.id}, true)">通过并设为当前</button>
                        <button class="action-btn action-approve" onclick="approveVersion(${version.id}, false)">仅通过</button>
                        <button class="action-btn action-reject" onclick="rejectVersion(${version.id})">拒绝</button>
                    </td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            versionsList.innerHTML = html;
        }
    });
}

function approveVersion(versionId, setAsCurrent) {
    fetch(`/admin/api/versions/${versionId}/approve?set_as_current=${setAsCurrent}`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('版本已通过审核');
            loadVersions();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function rejectVersion(versionId) {
    const reason = prompt('请输入拒绝原因（可选）：');
    
    const formData = new FormData();
    if (reason) formData.append('reason', reason);
    
    fetch(`/admin/api/versions/${versionId}/reject`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('版本已拒绝');
            loadVersions();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function loadReviews() {
    fetch('/admin/api/reviews?skip=0&limit=100', {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            const reviews = data.data;
            const reviewsList = document.getElementById('reviewsList');
            
            if (reviews.length === 0) {
                reviewsList.innerHTML = '<p style="padding: 40px; text-align: center; color: #64748b;">暂无评论</p>';
                return;
            }
            
            let html = '<tr><thead></tr>';
            html += '<th>ID</th><th>应用名称</th><th>用户</th><th>评分</th><th>标题</th><th>内容</th><th>点赞数</th><th>创建时间</th><th>操作</th>';
            html += '</thead><tbody>';
            
            reviews.forEach(review => {
                html += `<tr>
                    <td>${review.id}</td>
                    <td>${escapeHtml(review.app_name)}</td>
                    <td>${escapeHtml(review.user_name)}</td>
                    <td>${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)}</td>
                    <td>${escapeHtml(review.title || '')}<table>
                    <td>${escapeHtml(review.content || '')}</td>
                    <td>${review.like_count}</td>
                    <td>${new Date(review.created_at).toLocaleDateString()}</td>
                    <td class="action-btns">
                        <button class="action-btn action-reject" onclick="hideReview(${review.id})">隐藏</button>
                    </td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            reviewsList.innerHTML = html;
        }
    });
}

function hideReview(reviewId) {
    if (!confirm('确定要隐藏这条评论吗？')) return;
    
    fetch(`/admin/api/reviews/${reviewId}/hide`, {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            alert('评论已隐藏');
            loadReviews();
        } else {
            alert('操作失败：' + data.message);
        }
    });
}

function loadUsers() {
    fetch('/admin/api/users?skip=0&limit=100', {
        method: 'POST',
        headers: {
            'X-Admin-Password': adminPassword
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            const users = data.data;
            const usersList = document.getElementById('usersList');
            
            if (users.length === 0) {
                usersList.innerHTML = '<p style="padding: 40px; text-align: center; color: #64748b;">暂无用户</p>';
                return;
            }
            
            let html = '<table><thead><tr>';
            html += '<th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>应用数</th><th>评论数</th><th>注册时间</th><th>最后登录</th>';
            html += '</thead><tbody>';
            
            users.forEach(user => {
                html += `<tr>
                    <td>${user.id}</td>
                    <td>${escapeHtml(user.username)}</td>
                    <td>${user.email || '-'}</td>
                    <td>${user.role === 'admin' ? '管理员' : '普通用户'}</td>
                    <td>${user.apps_count}</td>
                    <td>${user.reviews_count}</td>
                    <td>${new Date(user.created_at).toLocaleDateString()}</td>
                    <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : '-'}</td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            usersList.innerHTML = html;
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}