from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass, asdict


@dataclass
class UploadTask:
    task_id: str
    user_id: int
    total: int
    current: int
    status: str  # 'uploading', 'completed', 'failed', 'cancelled'
    created_at: datetime
    updated_at: datetime
    success_items: list
    failed_items: list
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


class UploadTaskManager:
    """上传任务管理器（内存存储，线程安全）"""
    
    def __init__(self, cleanup_after_seconds: int = 300):
        self._tasks: Dict[str, UploadTask] = {}
        self._lock = threading.Lock()
        self._cleanup_after = cleanup_after_seconds
    
    def create_task(self, task_id: str, user_id: int, total: int) -> UploadTask:
        """创建新的上传任务"""
        with self._lock:
            # 检查是否已有该用户的活跃任务
            existing_active = any(
                task.user_id == user_id and task.status == 'uploading'
                for task in self._tasks.values()
            )
            if existing_active:
                print(f"[UploadManager] 用户{user_id}已有上传任务进行中，新任务{task_id}将并发执行")
            
            task = UploadTask(
                task_id=task_id,
                user_id=user_id,
                total=total,
                current=0,
                status='uploading',
                created_at=datetime.now(),
                updated_at=datetime.now(),
                success_items=[],
                failed_items=[]
            )
            self._tasks[task_id] = task
            print(f"[UploadManager] 创建任务: task_id={task_id}, user_id={user_id}, total={total}")
            return task
    
    def update_progress(
        self, 
        task_id: str, 
        current: int, 
        success_item: Optional[Dict] = None,
        failed_item: Optional[Dict] = None
    ):
        """更新任务进度"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            task.current = current
            task.updated_at = datetime.now()
            
            if success_item:
                task.success_items.append(success_item)
            if failed_item:
                task.failed_items.append(failed_item)
    
    def complete_task(self, task_id: str):
        """标记任务完成"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = 'completed'
                task.updated_at = datetime.now()
        # 任务完成后立即清理
        self._cleanup_completed_task(task_id)
    
    def _cleanup_completed_task(self, task_id: str):
        """完成后延迟清理任务（避免前端查询时任务已消失）"""
        import threading
        def delayed_cleanup():
            import time
            time.sleep(10)  # 10秒后清理，确保前端有时间查询到完成状态
            with self._lock:
                if task_id in self._tasks:
                    task = self._tasks[task_id]
                    if task.status in ['completed', 'failed', 'cancelled']:
                        del self._tasks[task_id]
        
        cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
        cleanup_thread.start()
    
    def fail_task(self, task_id: str):
        """标记任务失败"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = 'failed'
                task.updated_at = datetime.now()
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = 'cancelled'
                task.updated_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[UploadTask]:
        """获取任务信息"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_user_active_task(self, user_id: int) -> Optional[UploadTask]:
        """获取用户当前活跃的上传任务（正在上传中）"""
        with self._lock:
            # 按创建时间降序，返回最新的活跃任务
            active_tasks = [
                task for task in self._tasks.values()
                if task.user_id == user_id and task.status == 'uploading'
            ]
            if active_tasks:
                # 返回最新创建的任务
                return max(active_tasks, key=lambda t: t.created_at)
            return None
    
    def cleanup_old_tasks(self):
        """清理过期任务（自动调用）"""
        with self._lock:
            now = datetime.now()
            expired_ids = [
                task_id for task_id, task in self._tasks.items()
                if (now - task.updated_at).total_seconds() > self._cleanup_after
                and task.status in ['completed', 'failed', 'cancelled']
            ]
            for task_id in expired_ids:
                del self._tasks[task_id]
    
    def remove_task(self, task_id: str):
        """删除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]


# 全局单例
_upload_manager = UploadTaskManager(cleanup_after_seconds=300)


def get_upload_manager() -> UploadTaskManager:
    """获取上传任务管理器实例"""
    return _upload_manager
