import React from 'react';
import {View, Text, StyleSheet, ScrollView} from 'react-native';
import {useQuery} from '@tanstack/react-query';
import {useAuth} from '../contexts/AuthContext';
import {productsApi, salesApi, purchasesApi} from '../services/api';
import StatCard from '../components/StatCard';

const DashboardScreen: React.FC = () => {
  const {user} = useAuth();

  const {data: productsData} = useQuery({
    queryKey: ['products', 'count'],
    queryFn: () => productsApi.getAll({limit: 1}),
  });

  const {data: salesData} = useQuery({
    queryKey: ['sales', 'count'],
    queryFn: () => salesApi.getAll({limit: 1}),
  });

  const {data: purchasesData} = useQuery({
    queryKey: ['purchases', 'count'],
    queryFn: () => purchasesApi.getAll({limit: 1}),
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.welcomeText}>مرحباً، {user?.username}</Text>
        <Text style={styles.subtitle}>لوحة التحكم</Text>
      </View>

      <View style={styles.statsContainer}>
        <StatCard
          title="المنتجات"
          value={productsData?.total || 0}
          color="#4CAF50"
        />
        <StatCard
          title="المبيعات"
          value={salesData?.total || 0}
          color="#2196F3"
        />
        <StatCard
          title="المشتريات"
          value={purchasesData?.total || 0}
          color="#FF9800"
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  statsContainer: {
    padding: 15,
    gap: 15,
  },
});

export default DashboardScreen;

