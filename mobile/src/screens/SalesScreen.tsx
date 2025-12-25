import React from 'react';
import {View, Text, StyleSheet, FlatList, ActivityIndicator} from 'react-native';
import {useQuery} from '@tanstack/react-query';
import {salesApi} from '../services/api';

const SalesScreen: React.FC = () => {
  const {data, isLoading, error} = useQuery({
    queryKey: ['sales'],
    queryFn: () => salesApi.getAll(),
  });

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>حدث خطأ في تحميل البيانات</Text>
      </View>
    );
  }

  const renderItem = ({item}: {item: any}) => (
    <View style={styles.item}>
      <Text style={styles.itemInvoice}>فاتورة #{item.invoice_number}</Text>
      <Text style={styles.itemCustomer}>
        العميل: {item.customer_name || 'N/A'}
      </Text>
      <Text style={styles.itemAmount}>المجموع: {item.total_amount} ر.س</Text>
      <Text style={styles.itemStatus}>الحالة: {item.status}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>المبيعات</Text>
      </View>
      <FlatList
        data={data?.sales || []}
        renderItem={renderItem}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.list}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  list: {
    padding: 15,
  },
  item: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemInvoice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  itemCustomer: {
    fontSize: 16,
    color: '#666',
    marginBottom: 3,
  },
  itemAmount: {
    fontSize: 16,
    color: '#4CAF50',
    marginBottom: 3,
  },
  itemStatus: {
    fontSize: 14,
    color: '#666',
  },
  errorText: {
    fontSize: 16,
    color: '#f44336',
  },
});

export default SalesScreen;

