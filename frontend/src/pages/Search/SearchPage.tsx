import React, { useState } from 'react';
import { Input, Tabs, Table, Tag, Space, Empty } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { searchApi } from '../../api';
import type { SearchResultItem, SearchResponse } from '../../types';

const { Search } = Input;

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('all');
  const [results, setResults] = useState<SearchResponse | null>(null);

  const searchMutation = useMutation({
    mutationFn: (q: string) => searchApi.search({ query: q, scope, page: 1, page_size: 20 }),
    onSuccess: (data) => setResults(data),
  });

  const handleSearch = (value: string) => {
    if (!value.trim()) return;
    setQuery(value);
    searchMutation.mutate(value);
  };

  const columns = [
    {
      title: '类型', dataIndex: 'type', key: 'type', width: 80,
      render: (t: string) => <Tag color={t === 'ticket' ? 'blue' : 'green'}>{t === 'ticket' ? '工单' : '文章'}</Tag>,
    },
    {
      title: '标题', dataIndex: 'title', key: 'title',
      render: (title: string, r: SearchResultItem) => (
        <a onClick={() => r.type === 'ticket' ? navigate(`/tickets/${r.id}`) : navigate(`/kb/${r.id}/edit`)}>
          {title}
        </a>
      ),
    },
    {
      title: '匹配内容', dataIndex: 'snippet', key: 'snippet',
      render: (s: string) => <span dangerouslySetInnerHTML={{ __html: s }} />,
    },
    {
      title: '相关度', dataIndex: 'score', key: 'score', width: 80,
      render: (s: number) => s.toFixed(2),
    },
  ];

  return (
    <div>
      <Search
        placeholder="搜索工单和知识库文章..."
        enterButton={<><SearchOutlined /> 搜索</>}
        size="large"
        onSearch={handleSearch}
        loading={searchMutation.isPending}
        style={{ marginBottom: 24 }}
      />

      <Tabs
        activeKey={scope}
        onChange={(key) => {
          setScope(key);
          if (query) searchMutation.mutate(query);
        }}
        items={[
          { key: 'all', label: '全部' },
          { key: 'tickets', label: '工单' },
          { key: 'articles', label: '文章' },
        ]}
      />

      {results ? (
        <Table
          columns={columns}
          dataSource={results.items}
          rowKey="id"
          pagination={{ total: results.total, pageSize: 20 }}
          loading={searchMutation.isPending}
        />
      ) : (
        <Empty description="输入关键词开始搜索" />
      )}
    </div>
  );
};

export default SearchPage;
