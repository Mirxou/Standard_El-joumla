import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

interface StatCardProps {
  title: string;
  value: number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({title, value, color}) => {
  return (
    <View style={[styles.card, {borderLeftColor: color}]}>
      <Text style={styles.title}>{title}</Text>
      <Text style={[styles.value, {color}]}>{value}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 8,
    marginBottom: 10,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  value: {
    fontSize: 32,
    fontWeight: 'bold',
  },
});

export default StatCard;

