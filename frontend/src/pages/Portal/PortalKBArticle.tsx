import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Spin } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { portalKbApi } from '../../api/portal';

const PortalKBArticle: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const { data: article, isLoading } = useQuery({
    queryKey: ['portal-kb-article', slug],
    queryFn: () => portalKbApi.getArticle(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <Spin />;
  if (!article) return null;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/portal/kb')} style={{ marginBottom: 16 }}>
        返回帮助中心
      </Button>

      <Card title={article.title}>
        <div dangerouslySetInnerHTML={{ __html: article.body_html }} />
        {article.published_at && (
          <div style={{ marginTop: 24, color: '#999', fontSize: 12 }}>
            发布于: {new Date(article.published_at).toLocaleString()}
          </div>
        )}
      </Card>
    </div>
  );
};

export default PortalKBArticle;
