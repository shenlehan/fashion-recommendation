import { useState, useEffect, useRef } from "react";
import { flushSync } from "react-dom";
import { getUserWardrobe, uploadClothingItem, uploadClothingBatch, deleteClothingItem, deleteClothingBatch, getUploadStatus, API_ORIGIN } from "../services/api";
import "./Wardrobe.css";

// ===== 中英文映射字典 =====
const CATEGORY_MAP = {
  'top': '上装',
  'bottom': '下装',
  'dress': '连衣裙',
  'outerwear': '外套',
  'shoes': '鞋履',
  'accessories': '配饰',
  'unknown': '未知'
};

const SEASON_MAP = {
  'spring': '春季',
  'summer': '夏季',
  'fall': '秋季',
  'winter': '冬季'
};

const translateCategory = (category) => {
  return CATEGORY_MAP[category?.toLowerCase()] || category || '未分类';
};

const translateSeasons = (seasonStr) => {
  if (!seasonStr) return '未知';
  return seasonStr.split('/')
    .map(s => SEASON_MAP[s.trim().toLowerCase()] || s.trim())
    .join('/');
};

function Wardrobe({ user, setGlobalUpload, isUploading, abortControllerRef, isAbortedRef }) {
  const [wardrobe, setWardrobe] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const errorTimerRef = useRef(null); // 错误提示定时器
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    files: []
  });
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0, tick: 0 });
  const [selectedItems, setSelectedItems] = useState([]);
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [currentUploadIds, setCurrentUploadIds] = useState([]); // 记录本次上传成功的衣物ID
  const [isUploadFromRestore, setIsUploadFromRestore] = useState(false); // 标记是否从刷新恢复的上传
  const progressBarRef = useRef(null);
  const uploadedIdsRef = useRef([]); // 使用ref实时记录已上传ID，避免状态更新延迟
  const isUploadingGlobalRef = useRef(false); // 全局上传状态标记，防止重复上传

  // 监听error变化，5秒后自动清除
  useEffect(() => {
    if (error) {
      // 清除之前的定时器
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
      // 设置新的定时器
      errorTimerRef.current = setTimeout(() => {
        setError("");
      }, 5000);
    }
    return () => {
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
    };
  }, [error]);

  // 监听进度更新，直接操作DOM确保实时显示
  useEffect(() => {
    if (progressBarRef.current) {
      const percentage = uploadProgress.total > 0 
        ? (uploadProgress.current / uploadProgress.total) * 100 
        : 0;
      progressBarRef.current.style.width = `${percentage}%`;
    }
  }, [uploadProgress.tick]);

useEffect(() => {
    fetchWardrobe();
    checkUploadStatus(); // 检查是否有进行中的上传任务
  }, [user.id]);

  const checkUploadStatus = async () => {
    try {
      const statusData = await getUploadStatus(user.id);
      if (statusData.has_active_task) {
        const task = statusData.task;
        console.log('检测到进行中的上传任务:', task);
        
        // 标记为从刷新恢复
        setIsUploadFromRestore(true);
        
        // 设置全局上传标记
        isUploadingGlobalRef.current = true;
        
        // 恢复上传状态显示和取消能力
        const cancelHandler = () => {
          if (abortControllerRef.current) {
            isAbortedRef.current = true;
            abortControllerRef.current.abort();
          }
        };
        
        setGlobalUpload({
          uploading: true,
          progress: { current: task.current, total: task.total },
          onCancel: abortControllerRef.current ? cancelHandler : null
        });
        
        // 定时轮询更新状态，直到任务完成
        const pollInterval = setInterval(async () => {
          try {
            const latestStatus = await getUploadStatus(user.id);
            if (latestStatus.has_active_task) {
              const latestTask = latestStatus.task;
              setGlobalUpload(prev => ({
                ...prev,
                progress: { current: latestTask.current, total: latestTask.total }
              }));
              
              // 任务完成或失败，停止轮询
              if (latestTask.status === 'completed' || latestTask.status === 'failed' || latestTask.status === 'cancelled') {
                clearInterval(pollInterval);
                isUploadingGlobalRef.current = false; // 清除全局上传标记
                setGlobalUpload({ uploading: false, progress: { current: 0, total: 0 }, onCancel: null });
                setIsUploadFromRestore(false); // 清除恢复标记
                // 刷新衣橱显示最新上传的衣物
                await fetchWardrobe();
              }
            } else {
              // 任务不存在了，停止轮询
              clearInterval(pollInterval);
              isUploadingGlobalRef.current = false; // 清除全局上传标记
              setGlobalUpload({ uploading: false, progress: { current: 0, total: 0 }, onCancel: null });
              setIsUploadFromRestore(false); // 清除恢复标记
              await fetchWardrobe();
            }
          } catch (err) {
            console.error('轮询上传状态失败:', err);
          }
        }, 2000); // 每2秒轮询一次
        
        // 组件卸载时清理定时器
        return () => clearInterval(pollInterval);
      }
    } catch (err) {
      console.error('检查上传状态失败:', err);
    }
  };

  const fetchWardrobe = async () => {
    try {
      setLoading(true);
      const items = await getUserWardrobe(user.id);
      setWardrobe(items);
      setError("");
    } catch (err) {
      setError("加载衣橱失败");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setUploadForm({
      ...uploadForm,
      files: selectedFiles
    });
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (uploadForm.files.length === 0) {
      setError("请选择文件");
      return;
    }

    // 防止重复上传
    if (isUploadingGlobalRef.current) {
      setError("已有上传任务进行中，请稍后再试");
      return;
    }

    setUploading(true);
    isUploadingGlobalRef.current = true; // 设置全局上传标记
    setError("");
    setCurrentUploadIds([]); // 清空之前的记录
    uploadedIdsRef.current = []; // 清空ref记录
    isAbortedRef.current = false; // 重置取消标记
    setUploadProgress({ current: 0, total: uploadForm.files.length }); // 立即设置total，保证进度条显示

    // 创建AbortController
    abortControllerRef.current = new AbortController();

    // 同步全局上传状态
    const cancelHandler = () => {
      if (abortControllerRef.current) {
        isAbortedRef.current = true;
        abortControllerRef.current.abort();
      }
    };
    setGlobalUpload({
      uploading: true,
      progress: { current: 0, total: uploadForm.files.length },
      onCancel: cancelHandler
    });

    try {
      const formData = new FormData();
      
      // 批量上传：使用SSE实时进度
      if (uploadForm.files.length > 1) {
        uploadForm.files.forEach(file => {
          formData.append("files", file);
        });
        
        // 使用EventSource监听SSE
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6008/api/v1';
        const url = `${API_BASE_URL}/clothes/upload-batch-stream?user_id=${user.id}`;
        
        // 使用fetch手动处理SSE，并传入signal
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          signal: abortControllerRef.current.signal
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        let finalResult = { success: [], failed: [] };
        
        while (true) {
          // 检查是否已取消，立即跳出循环
          if (isAbortedRef.current) {
            console.log('检测到取消标记，立即终止SSE读取循环');
            break;
          }
          
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // 保留未完成的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.substring(6);
              const data = JSON.parse(jsonStr);
              
              if (data.type === 'start') {
                flushSync(() => {
                  setUploadProgress({ current: 0, total: data.total, tick: Date.now() });
                  setGlobalUpload(prev => ({ ...prev, progress: { current: 0, total: data.total } }));
                });
              } else if (data.type === 'progress') {
                // 收集成功上传的ID - 同时更新ref和state
                if (data.status === 'success' && data.item_id) {
                  uploadedIdsRef.current.push(data.item_id);
                  setCurrentUploadIds(prev => [...prev, data.item_id]);
                }
                flushSync(() => {
                  setUploadProgress({ current: data.current, total: data.total, tick: Date.now() });
                  setGlobalUpload(prev => ({ ...prev, progress: { current: data.current, total: data.total } }));
                });
              } else if (data.type === 'complete') {
                finalResult = data;
                // 收集所有成功的ID - 同时更新ref和state
                const successIds = data.success.map(item => item.item_id).filter(id => id);
                uploadedIdsRef.current.push(...successIds);
                setCurrentUploadIds(prev => [...prev, ...successIds]);
                flushSync(() => {
                  setUploadProgress({ current: data.total, total: data.total, tick: Date.now() });
                  setGlobalUpload(prev => ({ ...prev, progress: { current: data.total, total: data.total } }));
                });
              }
            }
          }
        }
        
        // 显示结果
        if (finalResult.failed.length > 0) {
          const failedNames = finalResult.failed.map(f => f.filename).join(", ");
          setError(`部分失败：${failedNames}`);
        }
        
        if (finalResult.success.length > 0) {
          setUploadForm({ files: [] });
          setShowUploadForm(false);
          setCurrentUploadIds([]); // 上传完成后清空ID列表
          uploadedIdsRef.current = []; // 清空ref
          // 全部上传完成后再刷新衣橱
          await fetchWardrobe();
        }
      } else {
        // 单个上传
        setUploadProgress({ current: 0, total: 1, tick: Date.now() });
        formData.append("file", uploadForm.files[0]);
        const result = await uploadClothingItem(user.id, formData);
        // 记录成功上传的ID - 同时更新ref和state
        if (result && result.item_id) {
          uploadedIdsRef.current = [result.item_id];
          setCurrentUploadIds([result.item_id]);
        }
        setUploadProgress({ current: 1, total: 1, tick: Date.now() });
        
        setUploadForm({ files: [] });
        setShowUploadForm(false);
        setCurrentUploadIds([]); // 上传完成后清空ID列表
        uploadedIdsRef.current = []; // 清空ref
        // 全部上传完成后再刷新衣橱
        await fetchWardrobe();
      }
    } catch (err) {
      // 如果是用户取消
      if (err.name === 'AbortError') {
        // 使用ref中的ID主动删除已上传的衣物
        const idsToDelete = uploadedIdsRef.current;
        console.log('取消上传，需要删除的ID:', idsToDelete);
        if (idsToDelete.length > 0) {
          try {
            await deleteClothingBatch(idsToDelete);
            setError(`已取消上传并删除 ${idsToDelete.length} 件已上传衣物`);
          } catch (deleteErr) {
            console.error('删除已上传衣物失败:', deleteErr);
            setError(`已取消上传，但删除 ${idsToDelete.length} 件衣物失败`);
          }
        } else {
          setError("已取消上传");
        }
        setUploadForm({ files: [] });
        setShowUploadForm(false);
        setCurrentUploadIds([]);
        uploadedIdsRef.current = [];
        // 取消时刷新衣橱，确保已删除的衣物不显示
        await fetchWardrobe();
      } else {
        console.error('上传错误:', err);
        setError(err.message || "上传失败");
      }
    } finally {
      isUploadingGlobalRef.current = false; // 清除全局上传标记
      setUploading(false);
      abortControllerRef.current = null;
      uploadedIdsRef.current = []; // 清理ref
      isAbortedRef.current = false; // 重置取消标记
      setGlobalUpload({ uploading: false, progress: { current: 0, total: 0 }, onCancel: null }); // 清空全局状态
      setTimeout(() => setUploadProgress({ current: 0, total: 0, tick: 0 }), 1000);
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm("确定要删除这件衣物吗？")) {
      return;
    }

    try {
      await deleteClothingItem(itemId);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      console.error('删除失败详情:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || '删除失败';
      setError(`删除失败: ${errorMsg}`);
    }
  };

  // 取消上传：立即中断请求
  const handleCancelUpload = async () => {
    // 如果是打开表单，检查是否有上传进行中
    if (!showUploadForm) {
      if (isUploading) {
        setError("有衣物正在上传中，请等待当前批次完成后再添加");
        return;
      }
      setShowUploadForm(true);
      return;
    }
    
    // 如果正在上传，立即中断请求
    if (uploading && abortControllerRef.current) {
      isAbortedRef.current = true; // 设置取消标记，立即停止SSE读取
      abortControllerRef.current.abort();
      return;
    }
    
    // 如果没有在上传，直接关闭表单
    setUploadForm({ files: [] });
    setShowUploadForm(false);
    setUploadProgress({ current: 0, total: 0, tick: 0 });
    setError("");
  };

  const toggleSelectionMode = () => {
    // 检查衣橱是否为空
    if (!isSelectionMode && wardrobe.length === 0) {
      setError("当前衣橱为空，请先添加衣物");
      return;
    }
    
    setIsSelectionMode(!isSelectionMode);
    setSelectedItems([]);
  };

  const toggleItemSelection = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleBatchDelete = async () => {
    if (selectedItems.length === 0) {
      setError("请选择要删除的衣物");
      return;
    }

    setShowDeleteConfirm(true);
  };

  const handleSelectAll = () => {
    if (selectedItems.length === wardrobe.length) {
      // 如果已全选，则取消全选
      setSelectedItems([]);
    } else {
      // 否则全选
      setSelectedItems(wardrobe.map(item => item.id));
    }
  };

  const confirmBatchDelete = async () => {
    setShowDeleteConfirm(false);

    try {
      const result = await deleteClothingBatch(selectedItems);
      
      if (result.failed.length > 0) {
        const failedIds = result.failed.map(f => f.item_id).join(", ");
        setError(`部分删除失败：ID ${failedIds}`);
      }
      
      if (result.success.length > 0) {
        setSelectedItems([]);
        setIsSelectionMode(false);
        fetchWardrobe();
      }
    } catch (err) {
      console.error('批量删除错误:', err);
      setError(err.message || "批量删除失败");
    }
  };

  const getImageUrl = (path, itemId) => {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    // 添加itemId作为缓存破坏参数，确保不同衣物的图片不会被错误缓存
    const baseUrl = `${API_ORIGIN}/${path.replace(/^\//, "")}`;
    return itemId ? `${baseUrl}?id=${itemId}` : baseUrl;
  };

  return (
    <div className="wardrobe-container">
      <div className="wardrobe-header">
        <h1>我的衣橱</h1>
        <div className="header-actions">
          {isSelectionMode ? (
            <>
              <span className="selection-count">已选 {selectedItems.length} 件</span>
              <button 
                className="btn-danger" 
                onClick={handleBatchDelete}
                disabled={selectedItems.length === 0}
              >
                删除所选
              </button>
              <button 
                className="btn-select-all" 
                onClick={handleSelectAll}
              >
                {selectedItems.length === wardrobe.length ? "取消全选" : "全选"}
              </button>
              <button
                className="btn-secondary"
                onClick={toggleSelectionMode}
              >
                取消选择
              </button>
            </>
          ) : (
            <>
              {!showUploadForm && (
                <button
                  className="btn-primary"
                  onClick={toggleSelectionMode}
                >
                  批量管理
                </button>
              )}
              <button
                className="btn-primary"
                onClick={handleCancelUpload}
              >
                {showUploadForm ? "取消" : "添加衣物"}
              </button>
            </>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>确认删除</h3>
            <p>确定要删除 <strong>{selectedItems.length}</strong> 件衣物吗？</p>
            <p className="modal-warning">此操作不可恢复</p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowDeleteConfirm(false)}>
                取消
              </button>
              <button className="btn-confirm-delete" onClick={confirmBatchDelete}>
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {showUploadForm && (
        <div className="upload-form">
          <h2>上传衣物</h2>
          <p className="upload-hint">AI 将自动识别并命名衣物，支持批量上传</p>
          <form onSubmit={handleUploadSubmit}>
            <div className="form-group">
              <label htmlFor="file">上传图片 *</label>
              <input
                type="file"
                id="file"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                required
                disabled={uploading}
              />
              {uploadForm.files.length > 0 && (
                <div className="file-preview-list">
                  <p className="file-count">已选择 {uploadForm.files.length} 个文件</p>
                  <ul>
                    {uploadForm.files.map((file, idx) => (
                      <li key={idx}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading 
                ? `正在处理 ${uploadProgress.current}/${uploadProgress.total} 个文件...` 
                : `上传 ${uploadForm.files.length || ''} 件衣物`
              }
            </button>
            
            {uploading && uploadProgress.total > 0 && (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div 
                    ref={progressBarRef}
                    className="progress-fill" 
                    style={{ 
                      width: '0%',
                      willChange: 'width'
                    }}
                  ></div>
                </div>
                <p className="progress-text">
                  {uploadProgress.current}/{uploadProgress.total} 完成 ({Math.round((uploadProgress.current / uploadProgress.total) * 100)}%)
                </p>
              </div>
            )}
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">加载中...</div>
      ) : wardrobe.length === 0 ? (
        <div className="empty-wardrobe">
          <p>你的衣橱还是空的，快来添加第一件衣物吧！</p>
        </div>
      ) : (
        <div className="wardrobe-grid">
          {wardrobe.map((item) => (
            <div 
              key={item.id} 
              className={`wardrobe-item ${isSelectionMode ? 'selectable' : ''} ${selectedItems.includes(item.id) ? 'selected' : ''}`}
              onClick={() => isSelectionMode && toggleItemSelection(item.id)}
            >
              {isSelectionMode && (
                <div className="selection-checkbox">
                  <input 
                    type="checkbox" 
                    checked={selectedItems.includes(item.id)}
                    onChange={() => toggleItemSelection(item.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              )}
              <div className="item-image">
                {item.image_path ? (
                  <img
                    src={getImageUrl(item.image_path, item.id)}
                    alt={item.name}
                  />
                ) : (
                  <div className="no-image">无图片</div>
                )}
              </div>
              <div className="item-details">
                <h3>{item.name}</h3>
                <div className="item-info">
                  <span className="badge">{translateCategory(item.category)}</span>
                  {item.color && <span className="badge color">{item.color}</span>}
                </div>
                {item.season && <p className="season">季节：{translateSeasons(item.season)}</p>}
                {item.material && <p className="material">材质：{item.material}</p>}
                {!isSelectionMode && (
                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(item.id)}
                  >
                    删除
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Wardrobe;
