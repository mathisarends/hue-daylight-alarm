import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface HeaderProps {
  title: string;
  onAddPress?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, onAddPress }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {onAddPress && (
        <TouchableOpacity style={styles.addButton} onPress={onAddPress}>
          <Ionicons name="add-circle-outline" size={28} color="#000" />
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  addButton: {
    padding: 4,
  },
});
