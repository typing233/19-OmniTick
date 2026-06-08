import React, { useState } from 'react';
import { Card, List, Input, Empty, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { portalKbApi } from '../../api/portal';

const { Search } = Input;

const PortalKBHome: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const { data: articles, isLoading } = useQuery({
    queryKey: ['portal-kb-articles'],
    queryFn: () => portalKbApi.listArticles({ page: 1, page_size: 50 }),
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ['portal-kb-search', searchQuery],
    queryFn: () => portalKbApi.search({ query: searchQuery }),
    enabled: searchQuery.length > 0,
  });

  const displayItems = searchQuery && searchResults ? searchResults.items : articles?.items;

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>帮助中心</h2>

      <Search
        placeholder="搜索文章..."
        size="large"
        enterButton={<><SearchOutlined /> 搜索</>}
        onSearch={setSearchQuery}
        style={{ marginBottom: 24 }}
      />

      {isLoading || searching ? (
        <Spin />
      ) : displayItems && displayItems.length > 0 ? (
        <List
          grid={{ gutter: 16, column: 2 }}
          dataSource={displayItems}
          renderItem={(item: { title: string; slug: string; snippet?: string }) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => navigate(`/portal/kb/${item.slug}`)}
                style={{ height: '100%' }}
              >
                <Card.Meta
                  title={item.title}
                  description={item.snippet ? <span dangerouslySetInnerHTML={{ __html: item.snippet }} /> : null}
                />
              </Card>
            </List.Item>
          )}
        />
      ) : (
        <Empty description="暂无文章" />
      )}
    </div>
  );
};

export default PortalKBHome;
