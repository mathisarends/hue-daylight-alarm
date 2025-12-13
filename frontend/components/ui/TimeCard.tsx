import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface TimeCardProps {
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
}

export const TimeCard: React.FC<TimeCardProps> = ({ title, subtitle, icon }) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <Ionicons name={icon} size={24} color="#000" />
      </View>
      <View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 16,
  },
  iconContainer: {
    width: 40,
    height: 40,
    backgroundColor: '#fff',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 12,
    color: '#666',
  },
});
