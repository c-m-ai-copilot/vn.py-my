def init_ui(self) -> None:
    # ... 其他代码保持不变 ...
    
    # 设置按钮样式
    self.setStyleSheet("""
        QPushButton {
            padding: 3px 6px;  /* 进一步减小内边距 */
            font-size: 11px;   /* 进一步减小字体大小 */
            min-width: 50px;   /* 进一步减小最小宽度 */
            height: 20px;      /* 减小高度 */
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 3px;
        }
        QPushButton:hover {
            background: #40a9ff;
        }
        QTableWidget {
            font-size: 12px;
        }
        QHeaderView::section {
            font-size: 12px;
            padding: 4px;
        }
    """) 